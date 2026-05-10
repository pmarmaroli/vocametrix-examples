"""
Stuttering Classification — Vocametrix API example

Classifies stuttering patterns in speech audio. This is an async endpoint:
  1. POST /api/classify-stuttering  → returns session_id
  2. Poll GET /api/therapy-status/:session_id  until complete
  3. Fetch GET /api/therapy-result/:session_id

The server timeout is 600 seconds (CLASSIFY_TIMEOUT_MS env var).
Response keys use lowercase_snake_case (Python-backed service).

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
            data={'email': 'user@example.com'},
        )
    r.raise_for_status()
    return r.json()['fileId']


def classify_stuttering(audio_path: str) -> dict:
    file_id = assign_file_id(audio_path)

    r = requests.post(
        f'{BASE_URL}/api/classify-stuttering',
        headers=HEADERS,
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
        print(f'  [{elapsed:3d}s] status: {state}')

        if state in ('completed', 'succeeded', 'done'):
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
    print(f"Stuttering detected: {results.get('stuttering_detected', 'N/A')}")
    print(f"Severity:            {results.get('severity', 'N/A')}")

    events = results.get('stuttering_events', [])
    if events:
        print(f'\nStuttering events ({len(events)} total):')
        for ev in events[:10]:
            onset = ev.get('onset', ev.get('start', '?'))
            etype = ev.get('type', '?')
            print(f'  {onset:.2f}s  type={etype}')

    for key in ('fluency_rate', 'speech_rate', 'processed_at'):
        if key in results:
            print(f"  {key}: {results[key]}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Stuttering classification')
    parser.add_argument('audio', help='Path to WAV file (connected speech)')
    args = parser.parse_args()

    results = classify_stuttering(args.audio)
    print_results(results)
