# JavaScript / Node.js examples

Runnable Node.js scripts for the Vocametrix API. Requires Node.js ≥ 18
(uses native `fetch`).

## Setup

```bash
npm install
# API key is read from ../.env at the repo root
```

## Scripts

| Script | Endpoint | Input |
|--------|----------|-------|
| `01-pronunciation-assessment.js` | `POST /api/pronunciation-assessment` | Any speech WAV |
| `02-speech-to-text-async.js` | `POST /api/offline-speech-to-text` + SSE | Any speech WAV |
| `03-text-to-speech.js` | `POST /api/text-to-speech` | — (text input) |
| `04-avqi-calculation.js` | `GET /api/calculate-avqi` | Sustained vowel |
| `05-dsi-calculation.js` | `GET /api/calculate-dsi` | Sustained vowel |
| `06-jitter-shimmer.js` | `GET /api/calculate-jitter-shimmer` | Sustained vowel |
| `07-phoneme-detection.js` | `POST /api/classify-phoneme` | Short phoneme sample |
| `08-stuttering-classification.js` | `POST /api/classify-stuttering` (async) | Connected speech |
| `09-prosody-similarity.js` | `GET /api/calculate-prosody-similarity` | Two WAV files |

## Workflows

See `workflows/` for end-to-end multi-step scripts.
