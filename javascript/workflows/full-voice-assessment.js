/**
 * Full Voice Assessment — Vocametrix API workflow (Node.js)
 *
 * Runs AVQI + DSI + CPP + HNR + jitter/shimmer in parallel from one
 * sustained-vowel and optional connected-speech recording.
 * Produces a single JSON clinical report.
 *
 * Usage:
 *   node full-voice-assessment.js sustained_vowel.wav
 *   node full-voice-assessment.js vowel.wav --connected speech.wav --output report.json
 */

import fs from 'fs';
import path from 'path';
import FormData from 'form-data';
import 'dotenv/config';

const API_KEY = process.env.VOCAMETRIX_API_KEY;
const BASE_URL = 'https://platform.vocametrix.com';
const HEADERS = { 'X-API-Key': API_KEY };

async function assignFileId(audioPath, label) {
  console.log(`  Uploading ${label}...`);
  const form = new FormData();
  form.append('audio', fs.createReadStream(audioPath));
  form.append('email', 'user@example.com');
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

async function buildReport(svPath, csPath) {
  const t0 = Date.now();
  console.log('Uploading audio files...');
  const svId = await assignFileId(svPath, 'sustained vowel');
  const csId = csPath ? await assignFileId(csPath, 'connected speech') : null;

  console.log('Running analyses in parallel...');
  const tasks = {
    avqi: () => getEndpoint('/api/calculate-avqi', csId ? { svFileId: svId, csFileId: csId } : { svFileId: svId }),
    dsi: () => getEndpoint('/api/calculate-dsi', { svFileId: svId }),
    cpp: () => getEndpoint('/api/calculate-cpp', { svFileId: svId }),
    hnr: () => getEndpoint('/api/calculate-hnr', { svFileId: svId }),
    jitter_shimmer: () => getEndpoint('/api/calculate-jitter-shimmer', { svFileId: svId }),
  };

  const results = {};
  const errors = {};
  await Promise.all(Object.entries(tasks).map(async ([name, fn]) => {
    try {
      results[name] = await fn();
      console.log(`  ✓ ${name}`);
    } catch (e) {
      errors[name] = e.message;
      console.log(`  ✗ ${name}: ${e.message}`);
    }
  }));

  const summary = {};
  if (results.avqi) {
    const avqi = results.avqi.AVQI;
    summary.AVQI = { value: avqi, classification: avqi != null && avqi < 2.97 ? 'Normal' : 'Dysphonic' };
  }
  if (results.dsi) {
    const dsi = results.dsi.DSI;
    summary.DSI = { value: dsi, classification: dsi != null && dsi > 1.6 ? 'Normal' : 'Possible dysphonia' };
  }
  if (results.jitter_shimmer) {
    const js = results.jitter_shimmer;
    summary['Jitter_%'] = js.JITTER_LOCAL_PERCENT ?? js.JITTER;
    summary['Shimmer_%'] = js.SHIMMER_LOCAL_PERCENT ?? js.SHIMMER;
  }
  if (results.cpp) summary.CPP_dB = results.cpp.CPP_MEAN ?? results.cpp.CPP;

  return {
    meta: {
      sustained_vowel: path.basename(svPath),
      connected_speech: csPath ? path.basename(csPath) : null,
      elapsed_seconds: ((Date.now() - t0) / 1000).toFixed(1),
    },
    summary,
    results,
    errors,
  };
}

// --- CLI ---
const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('Usage: node full-voice-assessment.js <sustained_vowel.wav> [--connected speech.wav] [--output report.json]');
  process.exit(1);
}
const svPath = args[0];
const csIdx = args.indexOf('--connected');
const outputIdx = args.indexOf('--output');
const csPath = csIdx !== -1 ? args[csIdx + 1] : null;
const outputPath = outputIdx !== -1 ? args[outputIdx + 1] : null;

buildReport(svPath, csPath).then(report => {
  console.log('\n=== Voice Assessment Report ===');
  for (const [k, v] of Object.entries(report.summary)) {
    if (typeof v === 'object') console.log(`  ${k}: ${v.value}  (${v.classification})`);
    else console.log(`  ${k}: ${v}`);
  }
  if (outputPath) {
    fs.writeFileSync(outputPath, JSON.stringify(report, null, 2));
    console.log(`\nFull report saved to ${outputPath}`);
  }
}).catch(err => { console.error(err.message); process.exit(1); });
