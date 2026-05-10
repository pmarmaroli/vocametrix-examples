# Python examples

Runnable Python scripts for the Vocametrix API. Each script handles its own
upload pattern and prints results to stdout.

## Setup

```bash
pip install -r requirements.txt
cp ../.env.example ../.env   # then add your VOCAMETRIX_API_KEY
```

## Generate test audio (optional)

```bash
python _generate_test_audio.py
# creates ../test_audio/sustained_vowel.wav, connected_speech.wav, glissando.wav
```

## Scripts

| Script | Endpoint | Input audio |
|--------|----------|-------------|
| `01_pronunciation_assessment.py` | `POST /api/pronunciation-assessment` | Any speech WAV |
| `02_speech_to_text_async.py` | `POST /api/offline-speech-to-text` + SSE | Any speech WAV |
| `03_text_to_speech.py` | `POST /api/text-to-speech` | — (text input) |
| `04_avqi_calculation.py` | `GET /api/calculate-avqi` | Sustained vowel |
| `05_dsi_calculation.py` | `GET /api/calculate-dsi` | Sustained vowel |
| `06_jitter_shimmer.py` | `GET /api/calculate-jitter-shimmer` | Sustained vowel |
| `07_phoneme_detection.py` | `POST /api/classify-phoneme` | Short phoneme sample |
| `08_stuttering_classification.py` | `POST /api/classify-stuttering` (async) | Connected speech |
| `09_prosody_similarity.py` | `GET /api/calculate-prosody-similarity` | Two WAV files |

## Workflows

See `workflows/` for end-to-end multi-step scripts:

- `batch_pronunciation_folder.py` — process a folder of WAV files, output CSV
- `full_voice_assessment.py` — AVQI + DSI + CPP + jitter/shimmer from two recordings
- `prosody_similarity_loop.py` — model vs N learners with pitch curve plots
