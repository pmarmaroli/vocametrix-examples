/**
 * Batch Pronunciation Assessment — Vocametrix API workflow (Node.js)
 *
 * Walks a folder of WAV files, runs pronunciation assessment on each,
 * writes results to a CSV. Uses exponential backoff for 429 rate limits.
 *
 * Usage:
 *   node batch-pronunciation-folder.js /path/to/wav/folder
 *   node batch-pronunciation-folder.js ./recordings --text "Say ah" --locale fr-FR --output results.csv --workers 4
 */

import fs from 'fs';
import path from 'path';
import { createWriteStream } from 'fs';
import FormData from 'form-data';
import 'dotenv/config';

const API_KEY = process.env.VOCAMETRIX_API_KEY;
const BASE_URL = 'https://platform.vocametrix.com';
const HEADERS = { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' };

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function uploadViaBlobUrl(audioPath) {
  const res = await fetch(`${BASE_URL}/api/get-blob-url`, { headers: HEADERS });
  if (!res.ok) throw new Error(`get-blob-url failed: ${await res.text()}`);
  const { uploadURL, blobURL } = await res.json();
  const put = await fetch(uploadURL, {
    method: 'PUT',
    body: fs.readFileSync(audioPath),
    headers: { 'x-ms-blob-type': 'BlockBlob', 'Content-Type': 'audio/wav' },
  });
  if (!put.ok) throw new Error(`Azure upload failed: ${await put.text()}`);
  return blobURL;
}

async function assessOne(audioPath, text, locale, maxRetries = 3) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const blobURL = await uploadViaBlobUrl(audioPath);
    const res = await fetch(`${BASE_URL}/api/pronunciation-assessment`, {
      method: 'POST',
      headers: HEADERS,
      body: JSON.stringify({ blobURL, referenceText: text, locale }),
    });
    if (res.status === 429) {
      const wait = (2 ** attempt) * 60_000;
      console.log(`  [${path.basename(audioPath)}] rate limited, waiting ${wait / 1000}s`);
      await sleep(wait);
      continue;
    }
    if (!res.ok) throw new Error(`pronunciation-assessment failed: ${await res.text()}`);
    return res.json();
  }
  throw new Error('Max retries exceeded');
}

async function processFolder(folder, text, locale, outputCsv, concurrency) {
  const files = fs.readdirSync(folder)
    .filter(f => f.toLowerCase().endsWith('.wav'))
    .sort()
    .map(f => path.join(folder, f));

  if (files.length === 0) { console.error('No WAV files found'); process.exit(1); }
  console.log(`Found ${files.length} files. Processing with concurrency=${concurrency}...`);

  const results = [];
  const errors = [];

  // Process in batches of `concurrency`
  for (let i = 0; i < files.length; i += concurrency) {
    const batch = files.slice(i, i + concurrency);
    await Promise.all(batch.map(async (fp) => {
      const name = path.basename(fp);
      try {
        const data = await assessOne(fp, text, locale);
        results.push({ file: name, accuracy: data.accuracyScore ?? '', fluency: data.fluencyScore ?? '',
                        completeness: data.completenessScore ?? '', pronunciation: data.pronunciationScore ?? '' });
        console.log(`  ✓ ${name.padEnd(40)}  accuracy=${data.accuracyScore ?? ''}`);
      } catch (e) {
        errors.push({ file: name, error: e.message });
        console.log(`  ✗ ${name}: ${e.message}`);
      }
    }));
  }

  results.sort((a, b) => a.file.localeCompare(b.file));

  const header = 'file,accuracy,fluency,completeness,pronunciation\n';
  const rows = results.map(r => `${r.file},${r.accuracy},${r.fluency},${r.completeness},${r.pronunciation}`).join('\n');
  fs.writeFileSync(outputCsv, header + rows + '\n', 'utf8');
  console.log(`\nWrote ${results.length} results to ${outputCsv}`);
  if (errors.length > 0) {
    console.log(`${errors.length} files failed:`);
    errors.forEach(e => console.log(`  ${e.file}: ${e.error}`));
  }
}

// --- CLI ---
const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('Usage: node batch-pronunciation-folder.js <folder> [--text "..."] [--locale en-US] [--output results.csv] [--workers 3]');
  process.exit(1);
}
const folder = args[0];
const textIdx = args.indexOf('--text');
const localeIdx = args.indexOf('--locale');
const outputIdx = args.indexOf('--output');
const workersIdx = args.indexOf('--workers');

processFolder(
  folder,
  textIdx !== -1 ? args[textIdx + 1] : 'Hello, my name is Alex.',
  localeIdx !== -1 ? args[localeIdx + 1] : 'en-US',
  outputIdx !== -1 ? args[outputIdx + 1] : 'pronunciation_results.csv',
  workersIdx !== -1 ? parseInt(args[workersIdx + 1]) : 3,
).catch(err => { console.error(err.message); process.exit(1); });
