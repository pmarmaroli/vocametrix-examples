"""
Jitter & Shimmer — Vocametrix API example

Measures perturbation in vocal fold vibration:
  Jitter  — cycle-to-cycle frequency variation (< 1.04% normal)
  Shimmer — cycle-to-cycle amplitude variation (< 3.81% normal)

Also returns HNR (Harmonics-to-Noise Ratio) and other perturbation measures.
Method: Teixeira & Gonçalves (2014) algorithm.

Upload pattern: POST /api/assignFileId → GET /api/calculate-jitter-shimmer
Auth: X-API-Key header

Usage:
    python 06_jitter_shimmer.py path/to/sustained_vowel.wav
"""

import os
import argparse
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
API_KEY = os.environ['VOCAMETRIX_API_KEY']
BASE_URL = 'https://platform.vocametrix.com'
HEADERS = {'X-API-Key': API_KEY}

# Clinical thresholds (based on Teixeira & Gonçalves 2014)
JITTER_THRESHOLD = 1.04   # percent
SHIMMER_THRESHOLD = 3.81  # percent


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


def calculate_jitter_shimmer(audio_path: str) -> dict:
    file_id = assign_file_id(audio_path)
    r = requests.get(
        f'{BASE_URL}/api/calculate-jitter-shimmer',
        headers=HEADERS,
        params={'svFileId': file_id},
    )
    r.raise_for_status()
    return r.json()


def print_results(results: dict):
    print('\n=== Jitter & Shimmer Results ===')

    jitter = results.get('JITTER_LOCAL_PERCENT', results.get('JITTER', 'N/A'))
    shimmer = results.get('SHIMMER_LOCAL_PERCENT', results.get('SHIMMER', 'N/A'))

    def flag(val, threshold):
        if not isinstance(val, (int, float)):
            return ''
        return '  ✓ normal' if val < threshold else '  ✗ elevated'

    print(f"Jitter (local):  {jitter}%{flag(jitter, JITTER_THRESHOLD)}")
    print(f"Shimmer (local): {shimmer}%{flag(shimmer, SHIMMER_THRESHOLD)}")

    for key in ('HNR', 'F0_MEAN', 'F0_SD', 'JITTER_RAP', 'SHIMMER_APQ3'):
        if key in results:
            print(f"  {key}: {results[key]}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Jitter and shimmer measurement')
    parser.add_argument('audio', help='Path to sustained-vowel WAV')
    args = parser.parse_args()

    results = calculate_jitter_shimmer(args.audio)
    print_results(results)
