/**
 * Phoneme Detection — Vocametrix API example (Node.js)
 *
 * Detects phonemes in speech audio. Returns predicted phoneme with confidence.
 * Supported languages: French (fr), Estonian (et).
 * Response keys are lowercase_snake_case (Python-backed service).
 *
 * Upload pattern: POST /api/assignFileId → POST /api/classify-phoneme
 * Auth: X-API-Key header
 *
 * Usage:
 *   node 07-phoneme-detection.js path/to/audio.wav
 *   node 07-phoneme-detection.js audio.wav --language et
 */

import fs from 'fs';
import FormData from 'form-data';
import 'dotenv/config';

const API_KEY = process.env.VOCAMETRIX_API_KEY;
const BASE_URL = 'https://platform.vocametrix.com';

async function assignFileId(audioPath) {
  const form = new FormData();
  form.append('audio', fs.createReadStream(audioPath));
  form.append('email', 'user@example.com');
  const res = await fetch(`${BASE_URL}/api/assignFileId`, {
    method: 'POST',
    headers: { 'X-API-Key': API_KEY, ...form.getHeaders() },
    body: form,
  });
  if (!res.ok) throw new Error(`assignFileId failed: ${await res.text()}`);
  return (await res.json()).fileId;
}

async function detectPhoneme(audioPath, language = 'fr') {
  const fileId = await assignFileId(audioPath);
  const res = await fetch(`${BASE_URL}/api/classify-phoneme`, {
    method: 'POST',
    headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({ fileId, language }),
  });
  if (!res.ok) throw new Error(`classify-phoneme failed: ${await res.text()}`);
  return res.json();
}

function printResults(results) {
  console.log('\n=== Phoneme Detection Results ===');
  console.log(`Predicted phoneme: ${results.predicted_phoneme ?? results.predicted_vowel ?? 'N/A'}`);
  console.log(`Confidence:        ${results.confidence ?? 'N/A'}`);
  console.log(`Language:          ${results.language ?? 'N/A'}`);

  const alts = results.top_predictions ?? results.alternatives ?? [];
  if (alts.length > 0) {
    console.log('\nTop predictions:');
    for (const alt of alts.slice(0, 5)) {
      const phoneme = alt.phoneme ?? alt.label ?? '?';
      const prob = alt.probability ?? alt.confidence ?? '?';
      console.log(`  ${phoneme.padEnd(8)}  ${prob}`);
    }
  }
}

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('Usage: node 07-phoneme-detection.js <audio.wav> [--language fr|et]');
  process.exit(1);
}
const audioPath = args[0];
const langIdx = args.indexOf('--language');
const language = langIdx !== -1 ? args[langIdx + 1] : 'fr';

detectPhoneme(audioPath, language).then(printResults).catch(err => { console.error(err.message); process.exit(1); });
