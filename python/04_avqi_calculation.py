"""
AVQI Calculation — Vocametrix API example

Computes the Acoustic Voice Quality Index (AVQI) — a clinically validated
composite measure of voice quality / dysphonia severity.

Reference: Maryn & Weenink (2015), Barsties & Maryn (2015)
  AVQI < 2.97  → normal voice quality
  AVQI ≥ 2.97  → dysphonic

Upload pattern: POST /api/assignFileId (multipart: audio + email) → GET /api/calculate-avqi
Auth: X-API-Key header

Usage:
    python 04_avqi_calculation.py path/to/sustained_vowel.wav
    python 04_avqi_calculation.py vowel.wav --connected connected_speech.wav
"""

import os
import argparse
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
API_KEY = os.environ['VOCAMETRIX_API_KEY']
BASE_URL = 'https://platform.vocametrix.com'
HEADERS = {'X-API-Key': API_KEY}

AVQI_THRESHOLD = 2.97


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


def calculate_avqi(sv_path: str, cs_path: str | None = None) -> dict:
    sv_id = assign_file_id(sv_path)
    params = {'svFileId': sv_id}

    if cs_path:
        cs_id = assign_file_id(cs_path)
        params['csFileId'] = cs_id

    r = requests.get(f'{BASE_URL}/api/calculate-avqi', headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()


def print_results(results: dict):
    avqi = results.get('AVQI', results.get('avqi', 'N/A'))
    print('\n=== AVQI Results ===')
    print(f"AVQI score: {avqi}")
    if isinstance(avqi, (int, float)):
        label = 'Normal' if avqi < AVQI_THRESHOLD else 'Dysphonic'
        print(f"Classification: {label}  (threshold: {AVQI_THRESHOLD})")

    for key in ('CPP', 'HNR05', 'HNR15', 'HNR25', 'HNR35', 'SHIM', 'SHDB', 'SHR'):
        if key in results:
            print(f"  {key}: {results[key]}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AVQI calculation')
    parser.add_argument('audio', help='Path to sustained-vowel WAV')
    parser.add_argument('--connected', help='Optional connected-speech WAV (improves accuracy)')
    args = parser.parse_args()

    results = calculate_avqi(args.audio, args.connected)
    print_results(results)
