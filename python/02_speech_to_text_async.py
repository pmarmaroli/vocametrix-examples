"""
Speech-to-Text (async SSE) — Vocametrix API example

Transcribes audio with word-level timing and confidence scores.
The transcription runs asynchronously; progress is streamed via SSE.

Upload pattern: get-blob-url → PUT to Azure → POST /api/offline-speech-to-text
Async pattern:  GET /api/transcription-progress/:id?apiKey=YOUR_KEY  (SSE)
  NOTE: The SSE endpoint authenticates via ?apiKey= query string, NOT the
  X-API-Key header. The browser EventSource API cannot send custom headers,
  so the backend accepts the key as a query param on this endpoint only.

Usage:
    python 02_speech_to_text_async.py path/to/audio.wav
    python 02_speech_to_text_async.py path/to/audio.wav --locale fr-FR
"""

import sys
import os
import json
import argparse
import requests
import sseclient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
API_KEY = os.environ['VOCAMETRIX_API_KEY']
BASE_URL = 'https://platform.vocametrix.com'
HEADERS = {'X-API-Key': API_KEY}


def upload_via_blob_url(audio_path: str) -> str:
    r = requests.post(f'{BASE_URL}/api/get-blob-url', headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    put = requests.put(
        data['uploadURL'],
        data=open(audio_path, 'rb'),
        headers={'x-ms-blob-type': 'BlockBlob', 'Content-Type': 'audio/wav'},
    )
    put.raise_for_status()
    return data['blobURL']


def transcribe(audio_path: str, locale: str) -> dict:
    blob_url = upload_via_blob_url(audio_path)

    r = requests.post(
        f'{BASE_URL}/api/offline-speech-to-text',
        headers=HEADERS,
        json={'blobUrl': blob_url, 'locale': locale},
    )
    r.raise_for_status()
    transcription_id = r.json()['transcriptionId']
    print(f'Transcription started: {transcription_id}')

    # SSE auth is via query string — X-API-Key header is ignored here
    sse_url = f'{BASE_URL}/api/transcription-progress/{transcription_id}?apiKey={API_KEY}'
    with requests.get(sse_url, stream=True) as resp:
        resp.raise_for_status()
        client = sseclient.SSEClient(resp)
        for event in client.events():
            if not event.data:
                continue
            payload = json.loads(event.data)
            status = payload.get('status', '')
            print(f'  status: {status}')
            if status == 'Succeeded':
                return payload
            if status.lower() == 'failed':
                raise RuntimeError(f'Transcription failed: {payload}')

    raise RuntimeError('SSE stream ended without a terminal status')


def print_results(result: dict):
    print('\n=== Transcription Results ===')
    print(f"Text: {result.get('displayText', result.get('text', 'N/A'))}")
    words = result.get('words', [])
    if words:
        print('\nWord-level timing:')
        for w in words[:20]:
            offset = w.get('offset', 0) / 1e7  # 100-ns ticks → seconds
            dur = w.get('duration', 0) / 1e7
            conf = w.get('confidence', '?')
            print(f"  {w.get('word', '?'):20s}  {offset:.2f}s  conf={conf}")
        if len(words) > 20:
            print(f'  ... and {len(words) - 20} more words')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Async speech-to-text')
    parser.add_argument('audio', help='Path to WAV file')
    parser.add_argument('--locale', default='en-US', help='Language locale')
    args = parser.parse_args()

    result = transcribe(args.audio, args.locale)
    print_results(result)
