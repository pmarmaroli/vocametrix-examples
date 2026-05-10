"""
Batch Pronunciation Assessment — Vocametrix API workflow

Walks a folder of WAV files, runs pronunciation assessment on each,
writes results to a CSV. Uses a thread pool with exponential backoff
for rate-limit resilience (API limit: 100 req/15 min).

Usage:
    python batch_pronunciation_folder.py /path/to/wav/folder
    python batch_pronunciation_folder.py ./recordings --text "Say ah" --locale fr-FR --output results.csv --workers 4
"""

import os
import sys
import csv
import time
import glob
import argparse
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
API_KEY = os.environ['VOCAMETRIX_API_KEY']
BASE_URL = 'https://platform.vocametrix.com'
HEADERS = {'X-API-Key': API_KEY}

_print_lock = threading.Lock()


def log(msg: str):
    with _print_lock:
        print(msg)


def upload_via_blob_url(audio_path: str) -> str:
    r = requests.post(f'{BASE_URL}/api/get-blob-url', headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    with open(audio_path, 'rb') as f:
        put = requests.put(
            data['uploadURL'],
            data=f,
            headers={'x-ms-blob-type': 'BlockBlob', 'Content-Type': 'audio/wav'},
        )
        put.raise_for_status()
    return data['blobURL']


def assess_one(audio_path: str, text: str, locale: str, max_retries: int = 3) -> dict:
    for attempt in range(max_retries + 1):
        try:
            blob_url = upload_via_blob_url(audio_path)
            r = requests.post(
                f'{BASE_URL}/api/pronunciation-assessment',
                headers=HEADERS,
                json={'blobURL': blob_url, 'referenceText': text, 'locale': locale},
            )
            if r.status_code == 429:
                wait = 2 ** attempt * 60  # exponential backoff: 60s, 120s, 240s
                log(f'  [{os.path.basename(audio_path)}] rate limited, waiting {wait}s (attempt {attempt + 1})')
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            if attempt == max_retries:
                raise
            wait = 2 ** attempt * 5
            log(f'  [{os.path.basename(audio_path)}] error: {e}, retrying in {wait}s')
            time.sleep(wait)


def process_folder(folder: str, text: str, locale: str, output_csv: str, workers: int):
    wav_files = sorted(glob.glob(os.path.join(folder, '*.wav')) +
                       glob.glob(os.path.join(folder, '*.WAV')))
    if not wav_files:
        print(f'No WAV files found in {folder}')
        sys.exit(1)

    print(f'Found {len(wav_files)} WAV files. Processing with {workers} workers...')

    results = []
    errors = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(assess_one, fp, text, locale): fp
            for fp in wav_files
        }
        for future in as_completed(futures):
            fp = futures[future]
            name = os.path.basename(fp)
            try:
                data = future.result()
                accuracy = data.get('accuracyScore', '')
                fluency = data.get('fluencyScore', '')
                completeness = data.get('completenessScore', '')
                pron = data.get('pronunciationScore', '')
                results.append({
                    'file': name,
                    'accuracy': accuracy,
                    'fluency': fluency,
                    'completeness': completeness,
                    'pronunciation': pron,
                })
                log(f'  ✓ {name:40s}  accuracy={accuracy}')
            except Exception as e:
                errors.append({'file': name, 'error': str(e)})
                log(f'  ✗ {name}: {e}')

    # Sort by filename for reproducible output
    results.sort(key=lambda r: r['file'])

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['file', 'accuracy', 'fluency', 'completeness', 'pronunciation'])
        writer.writeheader()
        writer.writerows(results)

    print(f'\nWrote {len(results)} results to {output_csv}')
    if errors:
        print(f'{len(errors)} files failed:')
        for e in errors:
            print(f'  {e["file"]}: {e["error"]}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch pronunciation assessment for a folder of WAV files')
    parser.add_argument('folder', help='Path to folder containing WAV files')
    parser.add_argument('--text', default='Hello, my name is Alex.', help='Reference text for all files')
    parser.add_argument('--locale', default='en-US', help='Language locale')
    parser.add_argument('--output', default='pronunciation_results.csv', help='Output CSV path')
    parser.add_argument('--workers', type=int, default=3, help='Number of parallel workers (default 3)')
    args = parser.parse_args()

    process_folder(args.folder, args.text, args.locale, args.output, args.workers)
