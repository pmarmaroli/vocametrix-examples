"""
Full Voice Assessment — Vocametrix API workflow

From one sustained-vowel and one connected-speech recording, runs
AVQI + DSI + CPP + multi-band HNR + jitter/shimmer in parallel and
produces a single JSON clinical report.

Usage:
    python full_voice_assessment.py sustained_vowel.wav connected_speech.wav
    python full_voice_assessment.py vowel.wav speech.wav --output report.json
"""

import os
import sys
import json
import time
import argparse
import concurrent.futures
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
API_KEY = os.environ['VOCAMETRIX_API_KEY']
BASE_URL = 'https://platform.vocametrix.com'
HEADERS = {'X-API-Key': API_KEY}


def assign_file_id(audio_path: str, label: str) -> str:
    print(f'  Uploading {label}...')
    with open(audio_path, 'rb') as f:
        r = requests.post(
            f'{BASE_URL}/api/assignFileId',
            headers=HEADERS,
            files={'audio': f},
        )
    r.raise_for_status()
    return r.json()['fileId']


def get(endpoint: str, params: dict) -> dict:
    r = requests.get(f'{BASE_URL}{endpoint}', headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()


def run_avqi(sv_id: str, cs_id: str | None) -> dict:
    params = {'svFileId': sv_id}
    if cs_id:
        params['csFileId'] = cs_id
    return get('/api/calculate-avqi', params)


def run_dsi(sv_id: str) -> dict:
    return get('/api/calculate-dsi', {'svFileId': sv_id})


def run_cpp(sv_id: str) -> dict:
    return get('/api/calculate-cpp', {'svFileId': sv_id})


def run_hnr(sv_id: str) -> dict:
    return get('/api/calculate-hnr-multiband', {'svFileId': sv_id})


def run_jitter_shimmer(sv_id: str) -> dict:
    return get('/api/jitter-shimmer', {'svFileId': sv_id})


def build_report(sv_path: str, cs_path: str | None) -> dict:
    t_start = time.time()
    print('Uploading audio files...')
    sv_id = assign_file_id(sv_path, 'sustained vowel')
    cs_id = assign_file_id(cs_path, 'connected speech') if cs_path else None

    print('Running analyses in parallel...')
    tasks = {
        'avqi': lambda: run_avqi(sv_id, cs_id),
        'dsi': lambda: run_dsi(sv_id),
        'cpp': lambda: run_cpp(sv_id),
        'hnr': lambda: run_hnr(sv_id),
        'jitter_shimmer': lambda: run_jitter_shimmer(sv_id),
    }

    results = {}
    errors = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(fn): name for name, fn in tasks.items()}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
                print(f'  ✓ {name}')
            except Exception as e:
                errors[name] = str(e)
                print(f'  ✗ {name}: {e}')

    elapsed = time.time() - t_start
    report = {
        'meta': {
            'sustained_vowel': os.path.basename(sv_path),
            'connected_speech': os.path.basename(cs_path) if cs_path else None,
            'elapsed_seconds': round(elapsed, 1),
        },
        'results': results,
        'errors': errors,
    }

    # Summarise key clinical values
    summary = {}
    if 'avqi' in results:
        avqi = results['avqi'].get('AVQI')
        summary['AVQI'] = {'value': avqi, 'classification': 'Normal' if avqi and avqi < 2.97 else 'Dysphonic'}
    if 'dsi' in results:
        dsi = results['dsi'].get('DSI')
        summary['DSI'] = {'value': dsi, 'classification': 'Normal' if dsi and dsi > 1.6 else 'Possible dysphonia'}
    if 'jitter_shimmer' in results:
        js = results['jitter_shimmer']
        j = js.get('JITTER_LOCAL_PERCENT', js.get('JITTER'))
        s = js.get('SHIMMER_LOCAL_PERCENT', js.get('SHIMMER'))
        summary['Jitter_%'] = j
        summary['Shimmer_%'] = s
    if 'cpp' in results:
        summary['CPP_dB'] = results['cpp'].get('CPP_MEAN', results['cpp'].get('CPP'))

    report['summary'] = summary
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Full voice assessment: AVQI + DSI + CPP + HNR + jitter/shimmer')
    parser.add_argument('sustained_vowel', help='Path to sustained-vowel WAV')
    parser.add_argument('connected_speech', nargs='?', help='Optional connected-speech WAV (improves AVQI)')
    parser.add_argument('--output', help='Save report to JSON file')
    args = parser.parse_args()

    report = build_report(args.sustained_vowel, args.connected_speech)

    print('\n=== Voice Assessment Report ===')
    for key, val in report['summary'].items():
        if isinstance(val, dict):
            print(f"  {key}: {val['value']}  ({val['classification']})")
        else:
            print(f"  {key}: {val}")

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f'\nFull report saved to {args.output}')
    else:
        print('\nFull results:')
        print(json.dumps(report['results'], indent=2))
