/**
 * Pronunciation Assessment — Vocametrix API example (Node.js)
 *
 * Scores how accurately a speaker pronounces a reference phrase.
 * Returns phoneme-level accuracy scores for 30+ locales.
 *
 * Upload pattern: get-blob-url → PUT to Azure → POST /api/pronunciation-assessment
 * Auth: X-API-Key header
 *
 * Usage:
 *   node 01-pronunciation-assessment.js path/to/audio.wav
 *   node 01-pronunciation-assessment.js audio.wav --text "Hello world" --locale en-US
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import 'dotenv/config';

const API_KEY = process.env.VOCAMETRIX_API_KEY;
const BASE_URL = 'https://platform.vocametrix.com';
const HEADERS = { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' };

async function uploadViaBlobUrl(audioPath) {
  const res = await fetch(`${BASE_URL}/api/get-blob-url`, { headers: HEADERS });
  if (!res.ok) throw new Error(`get-blob-url failed: ${await res.text()}`);
  const { uploadURL, blobURL } = await res.json();

  const audioData = fs.readFileSync(audioPath);
  const put = await fetch(uploadURL, {
    method: 'PUT',
    body: audioData,
    headers: { 'x-ms-blob-type': 'BlockBlob', 'Content-Type': 'audio/wav' },
  });
  if (!put.ok) throw new Error(`Azure upload failed: ${await put.text()}`);
  return blobURL;
}

async function assessPronunciation(audioPath, text, locale) {
  const blobURL = await uploadViaBlobUrl(audioPath);
  const res = await fetch(`${BASE_URL}/api/pronunciation-assessment`, {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify({ blobURL, referenceText: text, locale }),
  });
  if (!res.ok) throw new Error(`pronunciation-assessment failed: ${await res.text()}`);
  return res.json();
}

function printResults(results) {
  console.log('\n=== Pronunciation Assessment Results ===');
  console.log(`Overall accuracy:    ${results.accuracyScore?.toFixed(1) ?? 'N/A'} / 100`);
  console.log(`Fluency score:       ${results.fluencyScore?.toFixed(1) ?? 'N/A'} / 100`);
  console.log(`Completeness score:  ${results.completenessScore?.toFixed(1) ?? 'N/A'} / 100`);
  console.log(`Pronunciation score: ${results.pronunciationScore?.toFixed(1) ?? 'N/A'} / 100`);

  const words = results.words ?? [];
  if (words.length > 0) {
    console.log('\nWord-level breakdown:');
    for (const w of words) {
      console.log(`  ${w.word?.padEnd(20) ?? '?'}  accuracy=${w.accuracyScore?.toFixed(0) ?? '?'}`);
    }
  }
}

// --- CLI ---
const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('Usage: node 01-pronunciation-assessment.js <audio.wav> [--text "..."] [--locale en-US]');
  process.exit(1);
}
const audioPath = args[0];
const textIdx = args.indexOf('--text');
const localeIdx = args.indexOf('--locale');
const text = textIdx !== -1 ? args[textIdx + 1] : 'Hello, my name is Alex.';
const locale = localeIdx !== -1 ? args[localeIdx + 1] : 'en-US';

assessPronunciation(audioPath, text, locale)
  .then(printResults)
  .catch(err => { console.error(err.message); process.exit(1); });
