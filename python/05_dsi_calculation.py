"""
DSI Calculation — Vocametrix API example

Computes the Dysphonia Severity Index (DSI) — a multiparametric index
combining highest frequency, lowest intensity, maximum phonation time,
jitter, and shimmer into a single severity score.

  DSI >  1.6  → normal voice quality
  DSI <= 1.6  → possible dysphonia
  DSI <  0    → severe dysphonia

Upload pattern: POST /api/assignFileId → GET /api/calculate-dsi
Auth: X-API-Key header

Usage:
    python 05_dsi_calculation.py path/to/sustained_vowel.wav
"""

import os
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


def calculate_dsi(audio_path: str) -> dict:
    file_id = assign_file_id(audio_path)
    r = requests.get(
        f'{BASE_URL}/api/calculate-dsi',
        headers=HEADERS,
        params={'svFileId': file_id},
    )
    r.raise_for_status()
    return r.json()


def print_results(results: dict):
    dsi = results.get('DSI', 'N/A')
    print('\n=== DSI Results ===')
    print(f"DSI score: {dsi}")
    if isinstance(dsi, (int, float)):
        if dsi > 1.6:
            label = 'Normal'
        elif dsi > 0:
            label = 'Mild dysphonia'
        else:
            label = 'Severe dysphonia'
        print(f"Classification: {label}")

    for key in ('F0', 'JITTER', 'SHIMMER', 'MPT', 'HNR', 'INTENSITY_MIN'):
        if key in results:
            print(f"  {key}: {results[key]}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DSI calculation')
    parser.add_argument('audio', help='Path to sustained-vowel WAV')
    args = parser.parse_args()

    results = calculate_dsi(args.audio)
    print_results(results)
