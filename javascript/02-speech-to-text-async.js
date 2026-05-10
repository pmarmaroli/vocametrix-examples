/**
 * Speech-to-Text (async SSE) — Vocametrix API example (Node.js)
 *
 * Transcribes audio with word-level timing and confidence scores.
 * Progress is streamed via Server-Sent Events (SSE).
 *
 * NOTE: The SSE endpoint /api/transcription-progress/:id authenticates via
 * ?apiKey= query string. The X-API-Key header is IGNORED on this endpoint
 * because the browser EventSource API cannot send custom headers.
 *
 * Upload pattern: get-blob-url → PUT to Azure → POST /api/offline-speech-to-text
 * Async pattern:  GET /api/transcription-progress/:id?apiKey=KEY  (SSE)
 * Auth: X-API-Key header (except SSE — uses ?apiKey=)
 *
 * Usage:
 *   node 02-speech-to-text-async.js path/to/audio.wav
 *   node 02-speech-to-text-async.js audio.wav --locale fr-FR
 */

import fs from 'fs';
import EventSource from 'eventsource';
import 'dotenv/config';

const API_KEY = process.env.VOCAMETRIX_API_KEY;
const BASE_URL = 'https://platform.vocametrix.com';
const HEADERS = { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' };

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

async function transcribe(audioPath, locale) {
  const blobUrl = await uploadViaBlobUrl(audioPath);

  const res = await fetch(`${BASE_URL}/api/offline-speech-to-text`, {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify({ blobUrl, locale }),
  });
  if (!res.ok) throw new Error(`offline-speech-to-text failed: ${await res.text()}`);
  const { transcriptionId } = await res.json();
  console.log(`Transcription started: ${transcriptionId}`);

  // SSE auth is via query string only — X-API-Key header is ignored on this endpoint
  const sseUrl = `${BASE_URL}/api/transcription-progress/${transcriptionId}?apiKey=${API_KEY}`;

  return new Promise((resolve, reject) => {
    const es = new EventSource(sseUrl);
    es.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      const status = payload.status ?? '';
      console.log(`  status: ${status}`);
      if (status === 'Succeeded') {
        es.close();
        resolve(payload);
      } else if (status.toLowerCase() === 'failed') {
        es.close();
        reject(new Error(`Transcription failed: ${JSON.stringify(payload)}`));
      }
    };
    es.onerror = (err) => { es.close(); reject(new Error(`SSE error: ${JSON.stringify(err)}`)); };
  });
}

function printResults(result) {
  console.log('\n=== Transcription Results ===');
  console.log(`Text: ${result.displayText ?? result.text ?? 'N/A'}`);
  const words = result.words ?? [];
  if (words.length > 0) {
    console.log('\nWord-level timing (first 20):');
    for (const w of words.slice(0, 20)) {
      const offset = ((w.offset ?? 0) / 1e7).toFixed(2);
      console.log(`  ${(w.word ?? '?').padEnd(20)}  ${offset}s  conf=${w.confidence ?? '?'}`);
    }
    if (words.length > 20) console.log(`  ... and ${words.length - 20} more words`);
  }
}

// --- CLI ---
const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('Usage: node 02-speech-to-text-async.js <audio.wav> [--locale en-US]');
  process.exit(1);
}
const audioPath = args[0];
const localeIdx = args.indexOf('--locale');
const locale = localeIdx !== -1 ? args[localeIdx + 1] : 'en-US';

transcribe(audioPath, locale)
  .then(printResults)
  .catch(err => { console.error(err.message); process.exit(1); });
