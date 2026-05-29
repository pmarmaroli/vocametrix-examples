"""
Stuttering Classification — Vocametrix API example

Classifies stuttering patterns in speech audio. This is an async endpoint:
  1. POST /api/classify-stuttering  → returns session_id
  2. Poll GET /api/therapy-status/:session_id  until complete
  3. Fetch GET /api/therapy-result/:session_id

The server timeout is 600 seconds (CLASSIFY_TIMEOUT_MS env var).
The result has a ``classification`` array of ~4s blocks, each with a stutter
``primaryType``, a ``transcription``, and a ``words`` array of per-word timestamps.

Upload pattern: POST /api/assignFileId → POST /api/classify-stuttering (async)
Auth: X-API-Key header on all endpoints

Usage:
    python 08_stuttering_classification.py path/to/audio.wav
"""

import os
import time
import argparse
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
API_KEY = os.environ['VOCAMETRIX_API_KEY']
BASE_URL = 'https://platform.vocametrix.com'
HEADERS = {'X-API-Key': API_KEY}

POLL_INTERVAL = 5   # seconds between status checks
MAX_WAIT = 620      # slightly above server timeout


def assign_file_id(audio_path: str) -> str:
    with open(audio_path, 'rb') as f:
        r = requests.post(
            f'{BASE_URL}/api/assignFileId',
            headers=HEADERS,
            files={'audio': f},
        )
    r.raise_for_status()
    return r.json()['fileId']


def classify_stuttering(audio_path: str) -> dict:
    file_id = assign_file_id(audio_path)

    r = requests.post(
        f'{BASE_URL}/api/classify-stuttering',
        headers=HEADERS,
        # Optional flags: transcribe (default True -> adds per-word timestamps),
        # includePhonemes (default False -> set True for per-block phonetic output).
        json={'fileId': file_id},
    )
    r.raise_for_status()
    session_id = r.json()['session_id']
    print(f'Classification started: session_id={session_id}')

    # Poll for completion
    elapsed = 0
    while elapsed < MAX_WAIT:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

        status_r = requests.get(
            f'{BASE_URL}/api/therapy-status/{session_id}',
            headers=HEADERS,
        )
        status_r.raise_for_status()
        status = status_r.json()
        state = status.get('status', status.get('state', ''))
        progress = status.get('progress_percent', status.get('progress', ''))
        print(f'  [{elapsed:3d}s] {state} {progress}')

        if state == 'complete' or status.get('result_available'):
            break
        if state in ('failed', 'error'):
            raise RuntimeError(f'Classification failed: {status}')

    result_r = requests.get(
        f'{BASE_URL}/api/therapy-result/{session_id}',
        headers=HEADERS,
    )
    result_r.raise_for_status()
    return result_r.json()


def print_results(results: dict):
    print('\n=== Stuttering Classification Results ===')

    overall = results.get('overallClassification', {})
    if overall.get('primary_type'):
        print(f"Overall: {overall['primary_type']} ({overall.get('severity', '?')}) "
              f"- {overall.get('stuttering_percentage', '?')}% of speech stuttered")

    blocks = results.get('classification', [])
    print(f'\nBlocks ({len(blocks)}):')
    for b in blocks:
        print(f"\n  [{b.get('startTime')}s - {b.get('stopTime')}s]  "
              f"{b.get('primaryType')}  |  {b.get('transcription')!r}")
        # Per-word timestamps (present when transcribe=True, the default).
        for w in b.get('words', []):
            print(f"        {w['start']:.2f}s - {w['end']:.2f}s   {w['word']}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Stuttering classification')
    parser.add_argument('audio', help='Path to WAV file (connected speech)')
    args = parser.parse_args()

    results = classify_stuttering(args.audio)
    print_results(results)
