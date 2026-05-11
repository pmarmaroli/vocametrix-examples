"""
Prosody Similarity Loop — Vocametrix API workflow

Takes a model recording and N learner recordings, runs prosody similarity
for each pair, and plots the pitch curves with matplotlib.

Usage:
    python prosody_similarity_loop.py model.wav learner1.wav learner2.wav ...
    python prosody_similarity_loop.py model.wav ./learners/*.wav --output plot.png
"""

import os
import sys
import glob
import json
import argparse
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
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


def compare(model_id: str, learner_path: str) -> dict:
    learner_id = assign_file_id(learner_path)
    r = requests.get(
        f'{BASE_URL}/api/calculate-prosody-similarity',
        headers=HEADERS,
        params={'svFileId': model_id, 'csFileId': learner_id},
    )
    r.raise_for_status()
    return r.json()


def plot_curves(model_pitch: list, learner_results: list, output_path: str | None):
    try:
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
        import numpy as np
    except ImportError:
        print('matplotlib not installed — skipping plot. Run: pip install matplotlib')
        return

    fig, axes = plt.subplots(len(learner_results), 1,
                              figsize=(12, 4 * len(learner_results)),
                              squeeze=False)

    colors = cm.tab10(np.linspace(0, 1, len(learner_results)))

    for i, (name, result, color) in enumerate(zip(
        [r['name'] for r in learner_results],
        [r['result'] for r in learner_results],
        colors,
    )):
        ax = axes[i][0]
        lp = result.get('PITCH_CURVE_LEARNER', [])

        if model_pitch:
            ax.plot(model_pitch, color='black', linewidth=2, label='Model', linestyle='--')
        if lp:
            ax.plot(lp, color=color, linewidth=1.5, label=f'Learner: {name}')

        score = result.get('PROSODY_SIMILARITY_SCORE', result.get('similarity_score', '?'))
        ax.set_title(f'{name}  (similarity={score})')
        ax.set_xlabel('Time frame')
        ax.set_ylabel('F0 (Hz)')
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f'Plot saved to {output_path}')
    else:
        plt.show()


def run(model_path: str, learner_paths: list, output_path: str | None):
    print(f'Uploading model: {os.path.basename(model_path)}')
    model_id = assign_file_id(model_path)

    all_results = []
    model_pitch = None

    for lp in learner_paths:
        name = os.path.basename(lp)
        print(f'  Comparing learner: {name}')
        try:
            result = compare(model_id, lp)
            score = result.get('PROSODY_SIMILARITY_SCORE', result.get('similarity_score', 'N/A'))
            print(f'    similarity={score}')
            all_results.append({'name': name, 'result': result})
            if model_pitch is None:
                model_pitch = result.get('PITCH_CURVE_MODEL', [])
        except Exception as e:
            print(f'    ERROR: {e}')
            all_results.append({'name': name, 'result': {}, 'error': str(e)})

    print('\n=== Prosody Similarity Summary ===')
    for r in all_results:
        score = r['result'].get('PROSODY_SIMILARITY_SCORE',
                r['result'].get('similarity_score',
                r.get('error', 'N/A')))
        print(f"  {r['name']:40s}  {score}")

    if any(r.get('result') for r in all_results):
        plot_curves(model_pitch or [], all_results, output_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compare prosody of N learners against a model recording')
    parser.add_argument('model', help='Path to model/reference WAV')
    parser.add_argument('learners', nargs='+', help='Learner WAV file(s) or glob pattern')
    parser.add_argument('--output', help='Save plot to this PNG path (default: show interactively)')
    args = parser.parse_args()

    # Expand globs in case shell didn't expand them
    learner_files = []
    for pat in args.learners:
        expanded = glob.glob(pat)
        learner_files.extend(expanded if expanded else [pat])

    if not learner_files:
        print('No learner files found')
        sys.exit(1)

    run(args.model, learner_files, args.output)
