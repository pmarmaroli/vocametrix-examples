/**
 * AVQI Calculation — Vocametrix API example (Node.js)
 *
 * Computes the Acoustic Voice Quality Index (AVQI) — a clinically validated
 * composite measure of voice quality / dysphonia severity.
 *
 *   AVQI < 2.97  → normal voice quality
 *   AVQI ≥ 2.97  → dysphonic
 *
 * Upload pattern: POST /api/assignFileId → GET /api/calculate-avqi
 * Auth: X-API-Key header
 *
 * Usage:
 *   node 04-avqi-calculation.js sustained_vowel.wav
 *   node 04-avqi-calculation.js vowel.wav --connected speech.wav
 */

import fs from 'fs';
import FormData from 'form-data';
import 'dotenv/config';

const API_KEY = process.env.VOCAMETRIX_API_KEY;
const BASE_URL = 'https://platform.vocametrix.com';
const AVQI_THRESHOLD = 2.97;

async function assignFileId(audioPath) {
  const form = new FormData();
  form.append('audio', fs.createReadStream(audioPath));

  const res = await fetch(`${BASE_URL}/api/assignFileId`, {
    method: 'POST',
    headers: { 'X-API-Key': API_KEY, ...form.getHeaders() },
    body: form,
  });
  if (!res.ok) throw new Error(`assignFileId failed: ${await res.text()}`);
  return (await res.json()).fileId;
}

async function calculateAvqi(svPath, csPath) {
  const svFileId = await assignFileId(svPath);
  const params = new URLSearchParams({ svFileId });
  if (csPath) {
    const csFileId = await assignFileId(csPath);
    params.set('csFileId', csFileId);
  }

  const res = await fetch(`${BASE_URL}/api/calculate-avqi?${params}`, {
    headers: { 'X-API-Key': API_KEY },
  });
  if (!res.ok) throw new Error(`calculate-avqi failed: ${await res.text()}`);
  return res.json();
}

function printResults(results) {
  const avqi = results.AVQI ?? results.avqi ?? 'N/A';
  console.log('\n=== AVQI Results ===');
  console.log(`AVQI score: ${avqi}`);
  if (typeof avqi === 'number') {
    console.log(`Classification: ${avqi < AVQI_THRESHOLD ? 'Normal' : 'Dysphonic'}  (threshold: ${AVQI_THRESHOLD})`);
  }
  for (const key of ['CPP', 'HNR05', 'HNR15', 'HNR25', 'HNR35', 'SHIM', 'SHDB', 'SHR']) {
    if (results[key] !== undefined) console.log(`  ${key}: ${results[key]}`);
  }
}

// --- CLI ---
const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('Usage: node 04-avqi-calculation.js <sustained_vowel.wav> [--connected speech.wav]');
  process.exit(1);
}
const svPath = args[0];
const csIdx = args.indexOf('--connected');
const csPath = csIdx !== -1 ? args[csIdx + 1] : null;

calculateAvqi(svPath, csPath)
  .then(printResults)
  .catch(err => { console.error(err.message); process.exit(1); });
