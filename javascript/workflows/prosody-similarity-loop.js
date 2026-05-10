/**
 * Prosody Similarity Loop — Vocametrix API workflow (Node.js)
 *
 * Compares N learner recordings against a model recording.
 * Prints a similarity score summary. For plots, see the Python version
 * (prosody_similarity_loop.py) which includes matplotlib visualizations.
 *
 * Usage:
 *   node prosody-similarity-loop.js model.wav learner1.wav learner2.wav ...
 */

import fs from 'fs';
import path from 'path';
import FormData from 'form-data';
import 'dotenv/config';

const API_KEY = process.env.VOCAMETRIX_API_KEY;
const BASE_URL = 'https://platform.vocametrix.com';
const HEADERS = { 'X-API-Key': API_KEY };

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

async function compare(modelId, learnerPath) {
  const learnerId = await assignFileId(learnerPath);
  const res = await fetch(
    `${BASE_URL}/api/calculate-prosody-similarity?svFileId=${modelId}&csFileId=${learnerId}`,
    { headers: HEADERS },
  );
  if (!res.ok) throw new Error(`calculate-prosody-similarity failed: ${await res.text()}`);
  return res.json();
}

async function run(modelPath, learnerPaths) {
  console.log(`Uploading model: ${path.basename(modelPath)}`);
  const modelId = await assignFileId(modelPath);

  const summaryRows = [];
  for (const lp of learnerPaths) {
    const name = path.basename(lp);
    console.log(`  Comparing learner: ${name}`);
    try {
      const result = await compare(modelId, lp);
      const score = result.PROSODY_SIMILARITY_SCORE ?? result.similarity_score ?? 'N/A';
      console.log(`    similarity=${score}`);
      summaryRows.push({ name, score, pitchPoints: (result.PITCH_CURVE_LEARNER ?? []).length });
    } catch (e) {
      console.log(`    ERROR: ${e.message}`);
      summaryRows.push({ name, score: `ERROR: ${e.message}`, pitchPoints: 0 });
    }
  }

  console.log('\n=== Prosody Similarity Summary ===');
  for (const row of summaryRows) {
    console.log(`  ${row.name.padEnd(40)}  ${row.score}`);
  }
  console.log('\nFor pitch curve visualizations, use the Python version:');
  console.log('  python python/workflows/prosody_similarity_loop.py model.wav learner*.wav --output plot.png');
}

// --- CLI ---
const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: node prosody-similarity-loop.js <model.wav> <learner1.wav> [learner2.wav ...]');
  process.exit(1);
}
run(args[0], args.slice(1)).catch(err => { console.error(err.message); process.exit(1); });
