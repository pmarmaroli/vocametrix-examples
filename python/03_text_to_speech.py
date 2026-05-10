"""
Text-to-Speech — Vocametrix API example

Synthesizes speech from text and returns the audio with per-character
timing data (useful for karaoke highlighting or lip-sync animation).

Auth: X-API-Key header
Pattern: synchronous POST — audio returned directly in response

Usage:
    python 03_text_to_speech.py "Hello, this is a test."
    python 03_text_to_speech.py "Bonjour le monde" --locale fr-FR --output speech.wav
"""

import os
import json
import argparse
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
API_KEY = os.environ['VOCAMETRIX_API_KEY']
BASE_URL = 'https://platform.vocametrix.com'
HEADERS = {'X-API-Key': API_KEY}


def synthesize(text: str, locale: str, voice: str | None = None) -> dict:
    payload = {'text': text, 'locale': locale}
    if voice:
        payload['voiceName'] = voice

    r = requests.post(f'{BASE_URL}/api/text-to-speech', headers=HEADERS, json=payload)
    r.raise_for_status()
    return r.json()


def print_results(result: dict, output_path: str | None):
    print('\n=== Text-to-Speech Results ===')
    print(f"Duration: {result.get('audioDuration', 'N/A')} seconds")

    timing = result.get('charTimings', result.get('characterTimings', []))
    if timing:
        print(f'Character timings: {len(timing)} entries')
        print('First 5:')
        for entry in timing[:5]:
            print(f"  char={entry.get('char', '?')!r:4s}  offset={entry.get('audioOffset', 0) / 1e7:.3f}s")

    audio_b64 = result.get('audioData', result.get('audio', ''))
    if audio_b64 and output_path:
        import base64
        with open(output_path, 'wb') as f:
            f.write(base64.b64decode(audio_b64))
        print(f'\nAudio saved to {output_path}')
    elif audio_b64:
        print(f'\nAudio data returned ({len(audio_b64)} base64 chars). Pass --output to save.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Text-to-speech synthesis')
    parser.add_argument('text', help='Text to synthesize')
    parser.add_argument('--locale', default='en-US', help='Language locale')
    parser.add_argument('--voice', help='Voice name (optional)')
    parser.add_argument('--output', help='Save audio to this WAV path')
    args = parser.parse_args()

    result = synthesize(args.text, args.locale, args.voice)
    print_results(result, args.output)
