/**
 * Stuttering Classification — Vocametrix API example (Node.js)
 *
 * Classifies stuttering patterns in speech. Async endpoint:
 *   POST /api/classify-stuttering  → session_id
 *   Poll GET /api/therapy-status/:id  until complete
 *   Fetch GET /api/therapy-result/:id
 *
 * Server timeout: 600 seconds.
 * Response keys are lowercase_snake_case (Python-backed service).
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
  form.append('email', 'user@example.com');
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
    console.log(`  [${Math.round(elapsed / 1000)}s] status: ${state}`);

    if (['completed', 'succeeded', 'done'].includes(state)) break;
    if (['failed', 'error'].includes(state)) throw new Error(`Classification failed: ${JSON.stringify(status)}`);
  }

  const resultRes = await fetch(`${BASE_URL}/api/therapy-result/${session_id}`, { headers: HEADERS });
  if (!resultRes.ok) throw new Error(`therapy-result failed: ${await resultRes.text()}`);
  return resultRes.json();
}

function printResults(results) {
  console.log('\n=== Stuttering Classification Results ===');
  console.log(`Stuttering detected: ${results.stuttering_detected ?? 'N/A'}`);
  console.log(`Severity:            ${results.severity ?? 'N/A'}`);

  const events = results.stuttering_events ?? [];
  if (events.length > 0) {
    console.log(`\nStuttering events (${events.length} total):`);
    for (const ev of events.slice(0, 10)) {
      console.log(`  ${(ev.onset ?? ev.start ?? '?').toFixed?.(2) ?? '?'}s  type=${ev.type ?? '?'}`);
    }
  }
  for (const key of ['fluency_rate', 'speech_rate', 'processed_at']) {
    if (results[key] !== undefined) console.log(`  ${key}: ${results[key]}`);
  }
}

const audioPath = process.argv[2];
if (!audioPath) {
  console.error('Usage: node 08-stuttering-classification.js <audio.wav>');
  process.exit(1);
}
classifyStuttering(audioPath).then(printResults).catch(err => { console.error(err.message); process.exit(1); });
