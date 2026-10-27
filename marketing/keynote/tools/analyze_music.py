"""Tempo + energy map for candidate tracks (no librosa: onset envelope + autocorrelation)."""
import glob
import os
import subprocess
import sys

import numpy as np

SR = 22050


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def tempo(x):
    hop = 512
    frames = len(x) // hop
    e = np.array([np.sum(x[i * hop:(i + 1) * hop] ** 2) for i in range(frames)])
    onset = np.maximum(0, np.diff(np.log1p(e * 1000)))
    onset -= onset.mean()
    ac = np.correlate(onset, onset, "full")[len(onset) - 1:]
    fps = SR / hop
    lags = np.arange(len(ac))
    bpms = 60 * fps / np.maximum(lags, 1)
    ok = (bpms > 85) & (bpms < 170)
    best = lags[ok][np.argmax(ac[ok])]
    return 60 * fps / best


def energy_map(x, step=2.0):
    n = int(step * SR)
    return [float(np.sqrt(np.mean(x[i:i + n] ** 2))) for i in range(0, len(x) - n, n)]


for path in sorted(glob.glob(sys.argv[1] if len(sys.argv) > 1 else "*.mp3")):
    x = load(path)
    em = energy_map(x)
    peak = max(em) or 1
    bars = "".join(" .:-=+*#%@"[min(9, int(v / peak * 9.99))] for v in em)
    print(f"{os.path.basename(path):10s} {len(x) / SR:6.1f}s  {tempo(x):6.1f} BPM  |{bars}|")
