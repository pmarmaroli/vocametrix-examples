/**
 * Prosody Similarity — Vocametrix API example (Node.js)
 *
 * Compares pitch and intensity curves between a model (reference) speaker
 * and a learner speaker. Returns a similarity score and curve data.
 *
 * Upload pattern: POST /api/assignFileId for both files
 *                 → GET /api/calculate-prosody-similarity
 * Auth: X-API-Key header
 *
 * Usage:
 *   node 09-prosody-similarity.js model.wav learner.wav
 */

import fs from 'fs';
import FormData from 'form-data';
import 'dotenv/config';

const API_KEY = process.env.VOCAMETRIX_API_KEY;
const BASE_URL = 'https://platform.vocametrix.com';

async function assignFileId(audioPath, label) {
  console.log(`Uploading ${label}...`);
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

async function calculateProsodySimilarity(modelPath, learnerPath) {
  const svFileId = await assignFileId(modelPath, 'model');
  const csFileId = await assignFileId(learnerPath, 'learner');

  const res = await fetch(
    `${BASE_URL}/api/calculate-prosody-similarity?svFileId=${svFileId}&csFileId=${csFileId}`,
    { headers: { 'X-API-Key': API_KEY } },
  );
  if (!res.ok) throw new Error(`calculate-prosody-similarity failed: ${await res.text()}`);
  return res.json();
}

function printResults(results) {
  const score = results.PROSODY_SIMILARITY_SCORE ?? results.similarity_score ?? 'N/A';
  console.log('\n=== Prosody Similarity Results ===');
  console.log(`Overall similarity: ${score}`);
  for (const key of ['PITCH_CORRELATION', 'INTENSITY_CORRELATION', 'RHYTHM_SCORE']) {
    if (results[key] !== undefined) console.log(`  ${key}: ${results[key]}`);
  }
  const pitchModel = results.PITCH_CURVE_MODEL ?? [];
  const pitchLearner = results.PITCH_CURVE_LEARNER ?? [];
  if (pitchModel.length > 0) {
    console.log(`\nPitch curve points: ${pitchModel.length} (model), ${pitchLearner.length} (learner)`);
  }
}

const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: node 09-prosody-similarity.js <model.wav> <learner.wav>');
  process.exit(1);
}
calculateProsodySimilarity(args[0], args[1]).then(printResults).catch(err => { console.error(err.message); process.exit(1); });
