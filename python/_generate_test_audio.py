"""
Generate short synthetic WAV files for testing Vocametrix API examples.

Creates test_audio/ containing:
  sustained_vowel.wav  — 3 s steady 220 Hz sine (simulates /a/ phonation)
  connected_speech.wav — 4 s speech-shaped noise (for pronunciation/STT)
  glissando.wav        — 3 s frequency sweep 80 Hz → 600 Hz (for VRP/ambitus)

Usage:
    python python/_generate_test_audio.py
"""

import os
import numpy as np
from scipy.io import wavfile

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'test_audio')
RATE = 16000


def make_sustained_vowel(path, duration=3.0, freq=220.0):
    t = np.linspace(0, duration, int(RATE * duration), endpoint=False)
    # Fundamental + first two harmonics, light tremolo
    tremolo = 1.0 + 0.05 * np.sin(2 * np.pi * 5.5 * t)
    wave = tremolo * (
        0.6 * np.sin(2 * np.pi * freq * t)
        + 0.3 * np.sin(2 * np.pi * 2 * freq * t)
        + 0.1 * np.sin(2 * np.pi * 3 * freq * t)
    )
    wave = (wave / np.max(np.abs(wave)) * 0.8 * 32767).astype(np.int16)
    wavfile.write(path, RATE, wave)
    print(f"  wrote {path}")


def make_connected_speech(path, duration=4.0):
    rng = np.random.default_rng(42)
    t = np.linspace(0, duration, int(RATE * duration), endpoint=False)
    # Pink-ish noise shaped with a slow amplitude envelope (simulate syllables)
    noise = rng.standard_normal(len(t))
    # Low-pass: rough approximation via cumsum then diff
    noise = np.cumsum(noise)
    noise -= np.mean(noise)
    # Syllable envelope: 4 bumps
    env = np.zeros_like(t)
    for center in [0.5, 1.2, 2.1, 3.0]:
        env += np.exp(-((t - center) ** 2) / (2 * 0.15 ** 2))
    wave = noise * (env + 0.1)
    wave = (wave / np.max(np.abs(wave)) * 0.7 * 32767).astype(np.int16)
    wavfile.write(path, RATE, wave)
    print(f"  wrote {path}")


def make_glissando(path, duration=3.0, f_start=80.0, f_end=600.0):
    t = np.linspace(0, duration, int(RATE * duration), endpoint=False)
    # Exponential frequency sweep
    freq = f_start * (f_end / f_start) ** (t / duration)
    phase = 2 * np.pi * np.cumsum(freq) / RATE
    wave = 0.8 * np.sin(phase)
    wave = (wave / np.max(np.abs(wave)) * 0.8 * 32767).astype(np.int16)
    wavfile.write(path, RATE, wave)
    print(f"  wrote {path}")


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)
    print("Generating synthetic test audio files...")
    make_sustained_vowel(os.path.join(OUT_DIR, 'sustained_vowel.wav'))
    make_connected_speech(os.path.join(OUT_DIR, 'connected_speech.wav'))
    make_glissando(os.path.join(OUT_DIR, 'glissando.wav'))
    print("Done. Files are in test_audio/")
    print("NOTE: These are synthetic signals, not real speech.")
    print("      API results will be technically valid but not clinically meaningful.")
