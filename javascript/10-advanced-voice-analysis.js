/**
 * Advanced Voice Analysis — Vocametrix API example (Node.js)
 *
 * Runs advanced voice quality endpoints on a sustained vowel:
 *   H1*-H2*, Spectral, GNE, Formant statistics, ABI, Voice dynamics
 *
 * Upload pattern: POST /api/assignFileId → GET /api/calculate-*
 * Auth: X-API-Key header
 *
 * Usage:
 *   node 10-advanced-voice-analysis.js path/to/sustained_vowel.wav
 *   node 10-advanced-voice-analysis.js vowel.wav --gender 2
 */

import fs from 'fs';
import FormData from 'form-data';
import 'dotenv/config';

const API_KEY = process.env.VOCAMETRIX_API_KEY;
const BASE_URL = 'https://platform.vocametrix.com';
const HEADERS = { 'X-API-Key': API_KEY };

async function assignFileId(audioPath) {
  const form = new FormData();
  form.append('audio', fs.createReadStream(audioPath));
  const res = await fetch(`${BASE_URL}/api/assignFileId`, {
    method: 'POST',
    headers: { ...HEADERS, ...form.getHeaders() },
    body: form,
  });
  if (!res.ok) throw new Error(`assignFileId failed: ${await res.text()}`);
  return (await res.json()).fileId;
}

async function getEndpoint(endpoint, params) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE_URL}${endpoint}?${qs}`, { headers: HEADERS });
  if (!res.ok) throw new Error(`${endpoint} failed: ${await res.text()}`);
  return res.json();
}

async function runAdvanced(audioPath, gender) {
  console.log('Uploading sustained vowel...');
  const svId = await assignFileId(audioPath);
  const results = {};

  const endpoints = [
    ['h1h2',       '/api/calculate-h1-h2',              { svFileId: svId, gender }],
    ['spectral',   '/api/calculate-spectral-advanced',   { svFileId: svId, gender }],
    ['gne',        '/api/calculate-gne',                 { svFileId: svId }],
    ['formants',   '/api/calculate-formant-statistics',  { svFileId: svId, gender }],
    ['abi',        '/api/calculate-abi',                 { svFileId: svId }],
    ['dynamics',   '/api/calculate-voice-dynamics',      { svFileId: svId }],
  ];

  for (const [name, path, params] of endpoints) {
    console.log(`  ${name}...`);
    try {
      results[name] = await getEndpoint(path, params);
    } catch (e) {
      console.log(`  ✗ ${name}: ${e.message}`);
      results[name] = { error: e.message };
    }
  }
  return results;
}

function printResults(results) {
  console.log('\n=== Advanced Voice Analysis Results ===');
  for (const [section, data] of Object.entries(results)) {
    console.log(`\n--- ${section} ---`);
    for (const [key, val] of Object.entries(data)) {
      if (typeof val === 'object' && val !== null) {
        console.log(`  ${key}:`);
        for (const [k2, v2] of Object.entries(val)) {
          console.log(`    ${k2}: ${v2}`);
        }
      } else {
        console.log(`  ${key}: ${val}`);
      }
    }
  }
}

// --- CLI ---
const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('Usage: node 10-advanced-voice-analysis.js <sustained_vowel.wav> [--gender 1|2]');
  process.exit(1);
}
const audioPath = args[0];
const genderIdx = args.indexOf('--gender');
const gender = genderIdx !== -1 ? parseInt(args[genderIdx + 1]) : 1;

runAdvanced(audioPath, gender)
  .then(printResults)
  .catch(err => { console.error(err.message); process.exit(1); });
