/**
 * Stuttering Classification — Vocametrix API example (Node.js)
 *
 * Classifies stuttering patterns in speech. Async endpoint:
 *   POST /api/classify-stuttering  → session_id
 *   Poll GET /api/therapy-status/:id  until complete
 *   Fetch GET /api/therapy-result/:id
 *
 * Server timeout: 600 seconds.
 * The result has a `classification` array of ~4s blocks, each with a stutter
 * `primaryType`, a `transcription`, and a `words` array of per-word timestamps.
 *
 * Upload pattern: POST /api/assignFileId → POST /api/classify-stuttering
 * Auth: X-API-Key header
 *
 * Usage:
 *   node 08-stuttering-classification.js path/to/audio.wav
 */

import fs from 'fs';
import FormData from 'form-data';
import 'dotenv/config';

const API_KEY = process.env.VOCAMETRIX_API_KEY;
const BASE_URL = 'https://platform.vocametrix.com';
const HEADERS = { 'X-API-Key': API_KEY };
const POLL_INTERVAL_MS = 5000;
const MAX_WAIT_MS = 620_000;

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

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

async function classifyStuttering(audioPath) {
  const fileId = await assignFileId(audioPath);

  const startRes = await fetch(`${BASE_URL}/api/classify-stuttering`, {
    method: 'POST',
    headers: { ...HEADERS, 'Content-Type': 'application/json' },
    // Optional flags: transcribe (default true → adds per-word timestamps),
    // includePhonemes (default false → set true for per-block phonetic output).
    body: JSON.stringify({ fileId }),
  });
  if (!startRes.ok) throw new Error(`classify-stuttering failed: ${await startRes.text()}`);
  const { session_id } = await startRes.json();
  console.log(`Classification started: session_id=${session_id}`);

  let elapsed = 0;
  while (elapsed < MAX_WAIT_MS) {
    await sleep(POLL_INTERVAL_MS);
    elapsed += POLL_INTERVAL_MS;

    const statusRes = await fetch(`${BASE_URL}/api/therapy-status/${session_id}`, { headers: HEADERS });
    statusRes.raise_for_status?.();
    const status = await statusRes.json();
    const state = status.status ?? status.state ?? '';
    console.log(`  [${Math.round(elapsed / 1000)}s] ${state} ${status.progress_percent ?? status.progress ?? ''}`);

    if (state === 'complete' || status.result_available) break;
    if (['failed', 'error'].includes(state)) throw new Error(`Classification failed: ${JSON.stringify(status)}`);
  }

  const resultRes = await fetch(`${BASE_URL}/api/therapy-result/${session_id}`, { headers: HEADERS });
  if (!resultRes.ok) throw new Error(`therapy-result failed: ${await resultRes.text()}`);
  return resultRes.json();
}

function printResults(results) {
  console.log('\n=== Stuttering Classification Results ===');

  const overall = results.overallClassification ?? {};
  if (overall.primary_type) {
    console.log(`Overall: ${overall.primary_type} (${overall.severity ?? '?'}) - `
      + `${overall.stuttering_percentage ?? '?'}% of speech stuttered`);
  }

  const blocks = results.classification ?? [];
  console.log(`\nBlocks (${blocks.length}):`);
  for (const b of blocks) {
    console.log(`\n  [${b.startTime}s - ${b.stopTime}s]  ${b.primaryType}  |  ${JSON.stringify(b.transcription)}`);
    // Per-word timestamps (present when transcribe=true, the default).
    for (const w of b.words ?? []) {
      console.log(`        ${w.start.toFixed(2)}s - ${w.end.toFixed(2)}s   ${w.word}`);
    }
  }
}

const audioPath = process.argv[2];
if (!audioPath) {
  console.error('Usage: node 08-stuttering-classification.js <audio.wav>');
  process.exit(1);
}
classifyStuttering(audioPath).then(printResults).catch(err => { console.error(err.message); process.exit(1); });
