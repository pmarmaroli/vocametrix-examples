"""
AI Agents — Vocametrix API example

Demonstrates the AI agent endpoints — single-shot Azure AI Foundry agents
that accept JSON and return JSON. No audio upload required.

Available agents:
  - Therapy planning        (POST /api/therapy-planning-agent)
  - Speech exercise gen     (POST /api/speech-exercise-generator)
  - Syntax checker          (POST /api/syntax-checker-agent)
  - Spell checker           (POST /api/spell-agent)
  - Voice metrics interpret (POST /api/voice-metrics-interpreter)
  - Adaptive exercise       (POST /api/adaptive-exercise-agent)
  - French → IPA            (POST /api/french-to-ipa-agent)
  - Word list generator     (POST /api/word-list-generator)
  - Therapist assistant     (POST /api/speech-therapist-assistant)

Auth: X-API-Key header

Usage:
    python 11_ai_agents.py spell-check --text "The patint has a horase voice"
    python 11_ai_agents.py word-list --phoneme "ʃ" --locale fr-FR
    python 11_ai_agents.py interpret --metrics '{"AVQI": 3.5, "DSI": 0.8}'
    python 11_ai_agents.py therapist --query "What exercises help with /r/ articulation?"
"""

import os
import json
import argparse
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
API_KEY = os.environ['VOCAMETRIX_API_KEY']
BASE_URL = 'https://platform.vocametrix.com'
HEADERS = {'X-API-Key': API_KEY, 'Content-Type': 'application/json'}


def post(endpoint: str, body: dict) -> dict:
    r = requests.post(f'{BASE_URL}{endpoint}', headers=HEADERS, json=body)
    r.raise_for_status()
    return r.json()


def cmd_spell_check(args):
    result = post('/api/spell-agent', {'text': args.text, 'language': args.language})
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_syntax_check(args):
    result = post('/api/syntax-checker-agent', {'text': args.text, 'language': args.language})
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_word_list(args):
    result = post('/api/word-list-generator', {
        'targetPhoneme': args.phoneme,
        'difficulty': args.difficulty,
        'locale': args.locale,
    })
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_interpret(args):
    metrics = json.loads(args.metrics)
    body = {'metrics': metrics}
    if args.praat:
        body['praatResults'] = json.loads(args.praat)
    result = post('/api/voice-metrics-interpreter', body)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_therapist(args):
    body = {'query': args.query}
    if args.context:
        body['context'] = json.loads(args.context)
    result = post('/api/speech-therapist-assistant', body)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_french_to_ipa(args):
    phonetic_input = json.loads(args.input)
    result = post('/api/french-to-ipa-agent', {'phoneticInput': phonetic_input})
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_exercise(args):
    profile = json.loads(args.profile)
    result = post('/api/speech-exercise-generator', {
        'patientProfile': profile,
        'difficulty': args.difficulty,
    })
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Vocametrix AI agents')
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('spell-check', help='AI spell checker')
    p.add_argument('--text', required=True)
    p.add_argument('--language', default='en')
    p.set_defaults(func=cmd_spell_check)

    p = sub.add_parser('syntax-check', help='AI syntax checker')
    p.add_argument('--text', required=True)
    p.add_argument('--language', default='en')
    p.set_defaults(func=cmd_syntax_check)

    p = sub.add_parser('word-list', help='Generate word list targeting a phoneme')
    p.add_argument('--phoneme', required=True)
    p.add_argument('--difficulty', default='medium', choices=['easy', 'medium', 'hard'])
    p.add_argument('--locale', default='en-US')
    p.set_defaults(func=cmd_word_list)

    p = sub.add_parser('interpret', help='Interpret voice metrics in plain language')
    p.add_argument('--metrics', required=True, help='JSON object of metrics')
    p.add_argument('--praat', help='Optional JSON object of Praat results')
    p.set_defaults(func=cmd_interpret)

    p = sub.add_parser('therapist', help='Speech therapist AI assistant')
    p.add_argument('--query', required=True)
    p.add_argument('--context', help='Optional JSON context object')
    p.set_defaults(func=cmd_therapist)

    p = sub.add_parser('french-to-ipa', help='Convert French phonetic input to IPA')
    p.add_argument('--input', required=True, help='JSON array of phonetic input')
    p.set_defaults(func=cmd_french_to_ipa)

    p = sub.add_parser('exercise', help='Generate speech exercises')
    p.add_argument('--profile', required=True, help='JSON patient profile')
    p.add_argument('--difficulty', default='medium', choices=['easy', 'medium', 'hard'])
    p.set_defaults(func=cmd_exercise)

    args = parser.parse_args()
    args.func(args)
