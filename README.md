# vocametrix-examples

Runnable example code for the [Vocametrix API](https://www.vocametrix.com/api-docs) — voice analysis, speech therapy, and acoustic measurement endpoints used by speech-language pathologists, voice researchers, and developers building healthcare/education applications.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![API docs](https://img.shields.io/badge/API-docs-blue)](https://www.vocametrix.com/api-docs)

## What's in here

- **Python examples** (`python/`) — one runnable script per major endpoint group, plus end-to-end workflows
- **JavaScript / Node.js examples** (`javascript/`) — the same coverage, mirrored
- **Jupyter notebooks** (`notebooks/`) — batch analysis and visualization

## What you can do with the Vocametrix API

| Goal | Endpoint group |
|------|---------------|
| Score pronunciation accuracy (30+ locales, phoneme-level) | Pronunciation Assessment |
| Transcribe speech with word-level timing | Speech-to-Text (async SSE) |
| Synthesize speech with per-character alignment | Text-to-Speech |
| Compute AVQI — clinically validated dysphonia severity | AVQI Calculator |
| Compute DSI, CPP, multi-band HNR | Voice Quality Metrics |
| Jitter, shimmer, formants F1–F4, GNE, H1\*-H2\*, S/Z ratio, ABI | Advanced Voice Analysis |
| Voice Range Profile (ambitus / glissando) | VRP Analysis |
| Detect phonemes in real time (French, Estonian) | Phoneme Detection |
| Classify stuttering patterns | Stuttering Classification |
| Extract 88 openSMILE eGeMAPS features | eGeMAPS Extraction |
| Compare learner vs model prosody | Prosody Similarity |
| Generate a clinical therapy plan (LLM-backed, async) | Therapy Plan Generator |

Full endpoint reference: [https://www.vocametrix.com/api-docs](https://www.vocametrix.com/api-docs)  
OpenAPI 3.1 spec: [https://www.vocametrix.com/openapi.json](https://www.vocametrix.com/openapi.json)

## Quick start

### Python

```bash
git clone https://github.com/vocametrix/vocametrix-examples
cd vocametrix-examples

# Install dependencies
pip install -r python/requirements.txt

# Set your API key
cp .env.example .env
# edit .env and add your VOCAMETRIX_API_KEY

# Run your first example
python python/04_avqi_calculation.py path/to/sustained_vowel.wav
```

Get an API key at [https://www.vocametrix.com/registration](https://www.vocametrix.com/registration).

### JavaScript / Node.js

```bash
cd javascript
npm install

# API key is read from ../.env at the repo root
node 04-avqi-calculation.js path/to/sustained_vowel.wav
```

## Authentication

Every request requires an `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

**Exception:** The SSE progress endpoint `GET /api/transcription-progress/:id` uses a `?apiKey=` query string instead, because the browser `EventSource` API cannot send custom headers. All examples handle this automatically.

Get a key: [https://www.vocametrix.com/registration](https://www.vocametrix.com/registration)  
Pricing and rate limits: [https://www.vocametrix.com/pricing](https://www.vocametrix.com/pricing)

## Upload patterns

Two patterns exist — examples pick the right one automatically:

1. **`assignFileId` pattern** — used by all Praat-backed calculators (AVQI, DSI, CPP, HNR, spectral, formants, S/Z, GNE, H1\*-H2\*, VRP, jitter/shimmer, ABI, voice dynamics, prosody similarity, eGeMAPS, phoneme, stuttering, Estonian vowel):
   ```
   POST /api/assignFileId  (multipart: audio file + email)
   → returns { fileId }
   → pass fileId to the analysis endpoint
   ```

2. **`get-blob-url` pattern** — used by pronunciation assessment, speech-to-text, sound level:
   ```
   POST /api/get-blob-url
   → returns { uploadURL, blobURL }
   PUT <uploadURL>  (direct upload to Azure Blob Storage)
   POST /api/<analysis-endpoint>  (pass blobURL)
   ```

## Test audio files

The examples expect WAV files as input. You can:

- Use your own recordings
- Generate short synthetic test tones with the helper script:
  ```bash
  python python/_generate_test_audio.py
  # creates test_audio/ with: sustained_vowel.wav, connected_speech.wav, glissando.wav
  ```

No copyrighted audio is committed to this repository.

## Repository structure

```
vocametrix-examples/
├── .env.example                   # VOCAMETRIX_API_KEY=
├── python/
│   ├── requirements.txt
│   ├── _generate_test_audio.py    # synthetic test WAV generator
│   ├── 01_pronunciation_assessment.py
│   ├── 02_speech_to_text_async.py
│   ├── 03_text_to_speech.py
│   ├── 04_avqi_calculation.py
│   ├── 05_dsi_calculation.py
│   ├── 06_jitter_shimmer.py
│   ├── 07_phoneme_detection.py
│   ├── 08_stuttering_classification.py
│   ├── 09_prosody_similarity.py
│   └── workflows/
│       ├── batch_pronunciation_folder.py
│       ├── full_voice_assessment.py
│       └── prosody_similarity_loop.py
├── javascript/
│   ├── package.json
│   ├── 01-pronunciation-assessment.js
│   ├── 02-speech-to-text-async.js
│   ├── 03-text-to-speech.js
│   ├── 04-avqi-calculation.js
│   ├── 05-dsi-calculation.js
│   ├── 06-jitter-shimmer.js
│   ├── 07-phoneme-detection.js
│   ├── 08-stuttering-classification.js
│   ├── 09-prosody-similarity.js
│   └── workflows/
│       ├── batch-pronunciation-folder.js
│       ├── full-voice-assessment.js
│       └── prosody-similarity-loop.js
└── notebooks/
    ├── voice_quality_dashboard.ipynb
    └── prosody_similarity_visualization.ipynb
```

## Related projects

- **[API documentation](https://www.vocametrix.com/api-docs)** — full endpoint reference
- **[OpenAPI 3.1 spec](https://www.vocametrix.com/openapi.json)** — machine-validatable schema for typed client generation

## License

MIT — see [LICENSE](LICENSE).
