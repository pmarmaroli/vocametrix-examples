/**
 * AI Agents — Vocametrix API example (Node.js)
 *
 * Demonstrates the AI agent endpoints — single-shot JSON-in/JSON-out.
 * No audio upload required.
 *
 * Available agents:
 *   spell-check, syntax-check, word-list, interpret, therapist,
 *   french-to-ipa, exercise
 *
 * Auth: X-API-Key header
 *
 * Usage:
 *   node 11-ai-agents.js spell-check "The patint has a horase voice"
 *   node 11-ai-agents.js word-list --phoneme "ʃ" --locale fr-FR
 *   node 11-ai-agents.js interpret '{"AVQI": 3.5, "DSI": 0.8}'
 *   node 11-ai-agents.js therapist "What exercises help with /r/ articulation?"
 */

import 'dotenv/config';

const API_KEY = process.env.VOCAMETRIX_API_KEY;
const BASE_URL = 'https://platform.vocametrix.com';
const HEADERS = { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' };

async function post(endpoint, body) {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${endpoint} failed: ${await res.text()}`);
  return res.json();
}

const commands = {
  'spell-check': async (args) => {
    const text = args[0] ?? 'The patint has a horase voice';
    const langIdx = args.indexOf('--language');
    const language = langIdx !== -1 ? args[langIdx + 1] : 'en';
    return post('/api/spell-agent', { text, language });
  },

  'syntax-check': async (args) => {
    const text = args[0] ?? 'She go to the hospital yesterday.';
    const langIdx = args.indexOf('--language');
    const language = langIdx !== -1 ? args[langIdx + 1] : 'en';
    return post('/api/syntax-checker-agent', { text, language });
  },

  'word-list': async (args) => {
    const phonemeIdx = args.indexOf('--phoneme');
    const targetPhoneme = phonemeIdx !== -1 ? args[phonemeIdx + 1] : 'ʃ';
    const diffIdx = args.indexOf('--difficulty');
    const difficulty = diffIdx !== -1 ? args[diffIdx + 1] : 'medium';
    const localeIdx = args.indexOf('--locale');
    const locale = localeIdx !== -1 ? args[localeIdx + 1] : 'en-US';
    return post('/api/word-list-generator', { targetPhoneme, difficulty, locale });
  },

  'interpret': async (args) => {
    const metrics = JSON.parse(args[0] ?? '{"AVQI": 3.5}');
    return post('/api/voice-metrics-interpreter', { metrics });
  },

  'therapist': async (args) => {
    const query = args[0] ?? 'What exercises help with /r/ articulation?';
    return post('/api/speech-therapist-assistant', { query });
  },

  'french-to-ipa': async (args) => {
    const phoneticInput = JSON.parse(args[0] ?? '["bonjour"]');
    return post('/api/french-to-ipa-agent', { phoneticInput });
  },

  'exercise': async (args) => {
    const patientProfile = JSON.parse(args[0] ?? '{"age": 8, "diagnosis": "articulation disorder"}');
    const diffIdx = args.indexOf('--difficulty');
    const difficulty = diffIdx !== -1 ? args[diffIdx + 1] : 'medium';
    return post('/api/speech-exercise-generator', { patientProfile, difficulty });
  },
};

// --- CLI ---
const args = process.argv.slice(2);
const command = args[0];
if (!command || !commands[command]) {
  console.error(`Usage: node 11-ai-agents.js <command> [args...]`);
  console.error(`Commands: ${Object.keys(commands).join(', ')}`);
  process.exit(1);
}

commands[command](args.slice(1))
  .then(result => console.log(JSON.stringify(result, null, 2)))
  .catch(err => { console.error(err.message); process.exit(1); });
