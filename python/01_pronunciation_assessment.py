"""
Pronunciation Assessment — Vocametrix API example

Scores how accurately a speaker pronounces a reference phrase.
Returns phoneme-level accuracy scores for 30+ locales.

Upload pattern: get-blob-url → PUT to Azure → POST /api/pronunciation-assessment
Auth: X-API-Key header

Usage:
    python 01_pronunciation_assessment.py path/to/audio.wav
    python 01_pronunciation_assessment.py path/to/audio.wav --text "Hello world" --locale en-US
"""

import sys
import os
import json
import argparse
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
API_KEY = os.environ['VOCAMETRIX_API_KEY']
BASE_URL = 'https://platform.vocametrix.com'
HEADERS = {'X-API-Key': API_KEY}


def upload_via_blob_url(audio_path: str) -> str:
    """Upload audio through the Azure blob-url pattern, return blobURL."""
    r = requests.post(f'{BASE_URL}/api/get-blob-url', headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    upload_url = data['uploadURL']
    blob_url = data['blobURL']

    with open(audio_path, 'rb') as f:
        put = requests.put(
            upload_url,
            data=f,
            headers={'x-ms-blob-type': 'BlockBlob', 'Content-Type': 'audio/wav'},
        )
        put.raise_for_status()

    return blob_url


def assess_pronunciation(audio_path: str, text: str, locale: str) -> dict:
    blob_url = upload_via_blob_url(audio_path)

    r = requests.post(
        f'{BASE_URL}/api/pronunciation-assessment',
        headers=HEADERS,
        json={'blobURL': blob_url, 'referenceText': text, 'locale': locale},
    )
    r.raise_for_status()
    return r.json()


def print_results(results: dict):
    print('\n=== Pronunciation Assessment Results ===')
    print(f"Overall accuracy:    {results.get('accuracyScore', 'N/A'):.1f} / 100")
    print(f"Fluency score:       {results.get('fluencyScore', 'N/A'):.1f} / 100")
    print(f"Completeness score:  {results.get('completenessScore', 'N/A'):.1f} / 100")
    print(f"Pronunciation score: {results.get('pronunciationScore', 'N/A'):.1f} / 100")

    words = results.get('words', [])
    if words:
        print('\nWord-level breakdown:')
        for w in words:
            print(f"  {w.get('word', '?'):20s}  accuracy={w.get('accuracyScore', '?'):.0f}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pronunciation assessment')
    parser.add_argument('audio', help='Path to WAV file')
    parser.add_argument('--text', default='Hello, my name is Alex.', help='Reference text')
    parser.add_argument('--locale', default='en-US', help='Language locale (e.g. en-US, fr-FR)')
    args = parser.parse_args()

    results = assess_pronunciation(args.audio, args.text, args.locale)
    print_results(results)
