/**
 * Jitter & Shimmer — Vocametrix API example (Node.js)
 *
 * Measures cycle-to-cycle frequency (jitter) and amplitude (shimmer)
 * perturbation in vocal fold vibration. Clinical thresholds:
 *   Jitter  < 1.04%  → normal
 *   Shimmer < 3.81%  → normal
 *
 * Upload pattern: POST /api/assignFileId → GET /api/calculate-jitter-shimmer
 * Auth: X-API-Key header
 *
 * Usage:
 *   node 06-jitter-shimmer.js path/to/sustained_vowel.wav
 */

import fs from 'fs';
import FormData from 'form-data';
import 'dotenv/config';

const API_KEY = process.env.VOCAMETRIX_API_KEY;
const BASE_URL = 'https://platform.vocametrix.com';
const JITTER_THRESHOLD = 1.04;
const SHIMMER_THRESHOLD = 3.81;

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

async function calculateJitterShimmer(audioPath) {
  const svFileId = await assignFileId(audioPath);
  const res = await fetch(`${BASE_URL}/api/calculate-jitter-shimmer?svFileId=${svFileId}`, {
    headers: { 'X-API-Key': API_KEY },
  });
  if (!res.ok) throw new Error(`calculate-jitter-shimmer failed: ${await res.text()}`);
  return res.json();
}

function printResults(results) {
  const jitter = results.JITTER_LOCAL_PERCENT ?? results.JITTER ?? 'N/A';
  const shimmer = results.SHIMMER_LOCAL_PERCENT ?? results.SHIMMER ?? 'N/A';
  const flag = (val, thr) => typeof val === 'number' ? (val < thr ? '  ✓ normal' : '  ✗ elevated') : '';

  console.log('\n=== Jitter & Shimmer Results ===');
  console.log(`Jitter (local):  ${jitter}%${flag(jitter, JITTER_THRESHOLD)}`);
  console.log(`Shimmer (local): ${shimmer}%${flag(shimmer, SHIMMER_THRESHOLD)}`);
  for (const key of ['HNR', 'F0_MEAN', 'F0_SD', 'JITTER_RAP', 'SHIMMER_APQ3']) {
    if (results[key] !== undefined) console.log(`  ${key}: ${results[key]}`);
  }
}

const audioPath = process.argv[2];
if (!audioPath) {
  console.error('Usage: node 06-jitter-shimmer.js <sustained_vowel.wav>');
  process.exit(1);
}
calculateJitterShimmer(audioPath).then(printResults).catch(err => { console.error(err.message); process.exit(1); });
