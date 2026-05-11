"""
Advanced Voice Analysis — Vocametrix API example

Runs the advanced voice quality endpoints on a sustained vowel:
  - H1*-H2* (formant-corrected harmonic difference)
  - Spectral advanced (H1H2, H2H4, H4H2kHz, H2kHz5kHz)
  - GNE (Glottal-to-Noise Excitation ratio)
  - Formant statistics (F1, F2, F3 means and ranges)
  - ABI (Acoustic Breathiness Index)
  - Voice dynamics (perturbation over time)

For S/Z ratio, pass two recordings (sustained /s/ and sustained /z/).

Upload pattern: POST /api/assignFileId → GET /api/calculate-*
Auth: X-API-Key header

Usage:
    python 10_advanced_voice_analysis.py path/to/sustained_vowel.wav
    python 10_advanced_voice_analysis.py vowel.wav --gender 2
    python 10_advanced_voice_analysis.py /s/.wav --sz /z/.wav
"""

import os
import json
import argparse
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
API_KEY = os.environ['VOCAMETRIX_API_KEY']
BASE_URL = 'https://platform.vocametrix.com'
HEADERS = {'X-API-Key': API_KEY}


def assign_file_id(audio_path: str) -> str:
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


def run_advanced(audio_path: str, gender: int, sz_path: str | None):
    print('Uploading sustained vowel...')
    sv_id = assign_file_id(audio_path)

    results = {}

    print('  H1*-H2*...')
    results['h1h2'] = get('/api/calculate-h1-h2', {'svFileId': sv_id, 'gender': gender})

    print('  Spectral advanced...')
    results['spectral'] = get('/api/calculate-spectral-advanced', {'svFileId': sv_id, 'gender': gender})

    print('  GNE...')
    results['gne'] = get('/api/calculate-gne', {'svFileId': sv_id})

    print('  Formant statistics...')
    results['formants'] = get('/api/calculate-formant-statistics', {'svFileId': sv_id, 'gender': gender})

    print('  ABI...')
    results['abi'] = get('/api/calculate-abi', {'svFileId': sv_id})

    print('  Voice dynamics...')
    results['voice_dynamics'] = get('/api/calculate-voice-dynamics', {'svFileId': sv_id})

    if sz_path:
        print('Uploading /z/ recording...')
        cs_id = assign_file_id(sz_path)
        print('  S/Z ratio...')
        results['sz_ratio'] = get('/api/calculate-sz-ratio', {'svFileId': sv_id, 'csFileId': cs_id})

    return results


def print_results(results: dict):
    print('\n=== Advanced Voice Analysis Results ===')
    for section, data in results.items():
        print(f'\n--- {section} ---')
        for key, val in data.items():
            if isinstance(val, dict):
                print(f"  {key}:")
                for k2, v2 in val.items():
                    print(f"    {k2}: {v2}")
            else:
                print(f"  {key}: {val}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Advanced voice analysis')
    parser.add_argument('audio', help='Path to sustained-vowel WAV')
    parser.add_argument('--gender', type=int, default=1, choices=[1, 2],
                        help='1=male, 2=female (affects formant/spectral norms)')
    parser.add_argument('--sz', help='Optional /z/ WAV for S/Z ratio (audio arg = /s/)')
    args = parser.parse_args()

    results = run_advanced(args.audio, args.gender, args.sz)
    print_results(results)
