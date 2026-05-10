/**
 * DSI Calculation — Vocametrix API example (Node.js)
 *
 * Computes the Dysphonia Severity Index (DSI).
 *   DSI >  1.6  → normal
 *   DSI <= 1.6  → possible dysphonia
 *   DSI <  0    → severe dysphonia
 *
 * Upload pattern: POST /api/assignFileId → GET /api/calculate-dsi
 * Auth: X-API-Key header
 *
 * Usage:
 *   node 05-dsi-calculation.js path/to/sustained_vowel.wav
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

async function calculateDsi(audioPath) {
  const svFileId = await assignFileId(audioPath);
  const res = await fetch(`${BASE_URL}/api/calculate-dsi?svFileId=${svFileId}`, {
    headers: { 'X-API-Key': API_KEY },
  });
  if (!res.ok) throw new Error(`calculate-dsi failed: ${await res.text()}`);
  return res.json();
}

function printResults(results) {
  const dsi = results.DSI ?? 'N/A';
  console.log('\n=== DSI Results ===');
  console.log(`DSI score: ${dsi}`);
  if (typeof dsi === 'number') {
    const label = dsi > 1.6 ? 'Normal' : dsi > 0 ? 'Mild dysphonia' : 'Severe dysphonia';
    console.log(`Classification: ${label}`);
  }
  for (const key of ['F0', 'JITTER', 'SHIMMER', 'MPT', 'HNR', 'INTENSITY_MIN']) {
    if (results[key] !== undefined) console.log(`  ${key}: ${results[key]}`);
  }
}

const audioPath = process.argv[2];
if (!audioPath) {
  console.error('Usage: node 05-dsi-calculation.js <sustained_vowel.wav>');
  process.exit(1);
}
calculateDsi(audioPath).then(printResults).catch(err => { console.error(err.message); process.exit(1); });
