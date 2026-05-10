"""
Phoneme Detection — Vocametrix API example

Detects phonemes in speech audio. Returns predicted phoneme with confidence
and top-N alternative predictions.

Supported languages: French, Estonian
Response keys use lowercase_snake_case (Python-backed service).

Upload pattern: POST /api/assignFileId → POST /api/classify-phoneme
Auth: X-API-Key header

Usage:
    python 07_phoneme_detection.py path/to/audio.wav
    python 07_phoneme_detection.py path/to/audio.wav --language et
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
            data={'email': 'user@example.com'},
        )
    r.raise_for_status()
    return r.json()['fileId']


def detect_phoneme(audio_path: str, language: str = 'fr') -> dict:
    file_id = assign_file_id(audio_path)
    r = requests.post(
        f'{BASE_URL}/api/classify-phoneme',
        headers=HEADERS,
        json={'fileId': file_id, 'language': language},
    )
    r.raise_for_status()
    return r.json()


def print_results(results: dict):
    # Python-backed service returns lowercase_snake_case keys
    print('\n=== Phoneme Detection Results ===')
    print(f"Predicted phoneme: {results.get('predicted_phoneme', results.get('predicted_vowel', 'N/A'))}")
    print(f"Confidence:        {results.get('confidence', 'N/A')}")
    print(f"Language:          {results.get('language', 'N/A')}")

    alternatives = results.get('top_predictions', results.get('alternatives', []))
    if alternatives:
        print('\nTop predictions:')
        for alt in alternatives[:5]:
            phoneme = alt.get('phoneme', alt.get('label', '?'))
            prob = alt.get('probability', alt.get('confidence', '?'))
            print(f"  {phoneme:8s}  {prob}")

    if 'processed_at' in results:
        print(f"\nProcessed at: {results['processed_at']}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Phoneme detection')
    parser.add_argument('audio', help='Path to WAV file')
    parser.add_argument('--language', default='fr', choices=['fr', 'et'],
                        help='Language code: fr (French) or et (Estonian)')
    args = parser.parse_args()

    results = detect_phoneme(args.audio, args.language)
    print_results(results)
