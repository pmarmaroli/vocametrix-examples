/**
 * Text-to-Speech — Vocametrix API example (Node.js)
 *
 * Synthesizes speech and returns audio with per-character timing data.
 * Useful for karaoke highlighting or lip-sync animation.
 *
 * Auth: X-API-Key header
 * Pattern: synchronous POST
 *
 * Usage:
 *   node 03-text-to-speech.js "Hello, this is a test."
 *   node 03-text-to-speech.js "Bonjour" --locale fr-FR --output speech.wav
 */

import fs from 'fs';
import 'dotenv/config';

const API_KEY = process.env.VOCAMETRIX_API_KEY;
const BASE_URL = 'https://platform.vocametrix.com';
const HEADERS = { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' };

async function synthesize(text, locale, voice) {
  const body = { text, language: locale };
  if (voice) body.voice = voice;

  const res = await fetch(`${BASE_URL}/api/text-to-speech`, {
    method: 'POST',
    headers: HEADERS,
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`text-to-speech failed: ${await res.text()}`);
  return res.json();
}

function printResults(result, outputPath) {
  console.log('\n=== Text-to-Speech Results ===');
  console.log(`Duration: ${result.audioDuration ?? 'N/A'} seconds`);

  const timing = result.charTimings ?? result.characterTimings ?? [];
  if (timing.length > 0) {
    console.log(`Character timings: ${timing.length} entries`);
    console.log('First 5:');
    for (const entry of timing.slice(0, 5)) {
      const offset = ((entry.audioOffset ?? 0) / 1e7).toFixed(3);
      console.log(`  char=${JSON.stringify(entry.char ?? '?').padEnd(4)}  offset=${offset}s`);
    }
  }

  const audioB64 = result.audioData ?? result.audio ?? '';
  if (audioB64 && outputPath) {
    fs.writeFileSync(outputPath, Buffer.from(audioB64, 'base64'));
    console.log(`\nAudio saved to ${outputPath}`);
  } else if (audioB64) {
    console.log(`\nAudio data returned (${audioB64.length} base64 chars). Pass --output to save.`);
  }
}

// --- CLI ---
const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('Usage: node 03-text-to-speech.js <text> [--locale en-US] [--voice name] [--output file.wav]');
  process.exit(1);
}
const text = args[0];
const localeIdx = args.indexOf('--locale');
const voiceIdx = args.indexOf('--voice');
const outputIdx = args.indexOf('--output');
const locale = localeIdx !== -1 ? args[localeIdx + 1] : 'en-US';
const voice = voiceIdx !== -1 ? args[voiceIdx + 1] : null;
const output = outputIdx !== -1 ? args[outputIdx + 1] : null;

synthesize(text, locale, voice)
  .then(r => printResults(r, output))
  .catch(err => { console.error(err.message); process.exit(1); });
