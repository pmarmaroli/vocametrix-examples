"""
Prosody Similarity — Vocametrix API example

Compares pitch and intensity curves between a model (reference) speaker
and a learner speaker. Returns a similarity score and curve data.

Upload pattern: POST /api/assignFileId for both files
                → GET /api/calculate-prosody-similarity
Auth: X-API-Key header

Usage:
    python 09_prosody_similarity.py model.wav learner.wav
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


def calculate_prosody_similarity(model_path: str, learner_path: str) -> dict:
    print('Uploading model recording...')
    model_id = assign_file_id(model_path)
    print('Uploading learner recording...')
    learner_id = assign_file_id(learner_path)

    r = requests.get(
        f'{BASE_URL}/api/calculate-prosody-similarity',
        headers=HEADERS,
        params={'svFileId': model_id, 'csFileId': learner_id},
    )
    r.raise_for_status()
    return r.json()


def print_results(results: dict):
    print('\n=== Prosody Similarity Results ===')
    score = results.get('PROSODY_SIMILARITY_SCORE', results.get('similarity_score', 'N/A'))
    print(f"Overall similarity: {score}")

    for key in ('PITCH_CORRELATION', 'INTENSITY_CORRELATION', 'RHYTHM_SCORE'):
        if key in results:
            print(f"  {key}: {results[key]}")

    # Curve data is available for visualization
    pitch_model = results.get('PITCH_CURVE_MODEL', [])
    pitch_learner = results.get('PITCH_CURVE_LEARNER', [])
    if pitch_model and pitch_learner:
        print(f"\nPitch curve points: {len(pitch_model)} (model), {len(pitch_learner)} (learner)")
        print("  (Pass results to prosody_similarity_loop.py workflow for visualization)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Prosody similarity analysis')
    parser.add_argument('model', help='Path to model/reference WAV')
    parser.add_argument('learner', help='Path to learner WAV')
    args = parser.parse_args()

    results = calculate_prosody_similarity(args.model, args.learner)
    print_results(results)
