"""Soundtrack for "Find.": music edited to the beat map + a Mixkit SFX for every event, each
placed by its measured peak. Output: build/soundtrack.wav (loudnorm -14 LUFS).

Music (Mixkit "New Bass 02", stretched 117.5 -> 120 BPM, drop measured at D):
  film 0.0-21.5  = track [D-6, D+15.5]      -> the drop lands on beat 12 (6.0 s)
  film 21.5-25.0 = track [2.0, 5.5]         -> quiet intro as the breakdown (wall)
  film 25.0-27.0 = track [D+16, D+18]       -> a downbeat for the wordmark's return
"""
import os
import subprocess
import wave

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SFX = os.path.join(ROOT, "assets", "audio", "sfx")
SR = 44100
DUR = 27.0
D = 16.09          # measured drop onset in build/music_120.wav
B = 0.5            # one beat


def load(path, max_len=None):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    if max_len and len(x) > max_len * SR:
        x = x[: int(max_len * SR)]
        fade = int(0.25 * SR)
        x[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return x


def peak_time(x):
    """Time of the loudest 10 ms window (where the hit actually lands)."""
    hop = int(0.01 * SR)
    e = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, max(1, len(x) - hop), hop)])
    return int(np.argmax(e)) * 0.01


def place(buf, x, event_t, gain):
    start = int((event_t - peak_time(x)) * SR)
    if start < 0:
        x = x[-start:]
        start = 0
    end = min(len(buf), start + len(x))
    buf[start:end] += x[: end - start] * gain


def music():
    m = load(os.path.join(ROOT, "build", "music_120.wav"))
    seg = lambda a, b: m[int(a * SR): int(b * SR)]
    parts = [seg(D - 6.0, D + 15.5), seg(2.0, 5.5), seg(D + 16.0, D + 18.0)]
    xf = int(0.015 * SR)
    out = parts[0]
    for p in parts[1:]:
        p = p.copy()
        out = out.copy()
        out[-xf:] *= np.linspace(1, 0, xf)[:, None]
        p[:xf] *= np.linspace(0, 1, xf)[:, None]
        out = np.concatenate([out[:-xf], out[-xf:] + p[:xf], p[xf:]])
    out = out[: int(DUR * SR)]
    fade = int(0.6 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    return out


# (beat, sfx file, gain, max length s)
EVENTS = [
    (1.0, "sweep_small", 0.5, None), (2.0, "pop_long", 0.6, None), (3.0, "pop_light", 0.45, None), (4.0, "click_ui", 0.9, None),
    (5.0, "shutter_lens", 0.7, None), (6.0, "shutter_digital", 0.7, None), (7.0, "pop_light", 0.5, None),
    (8.0, "sweep_small", 0.5, None), (9.0, "sweep_small", 0.5, None), (10.0, "whoosh_fast", 0.55, None), (11.0, "click_select", 0.8, None),
    (12.0, "impact_deep", 0.75, 1.8),
    (13.0, "pop_bubble", 0.35, None), (13.14, "pop_bubble", 0.3, None), (13.28, "pop_bubble", 0.3, None), (13.42, "pop_bubble", 0.3, None),
    (14.0, "drop_liquid", 0.6, None), (15.0, "drop_water", 0.6, None), (16.0, "click_ui", 0.9, None), (17.0, "swoosh_wind", 0.45, None),
    (17.7, "glass_clink", 0.45, None), (19.0, "pop_long", 0.55, None), (20.0, "shutter_lens", 0.6, None), (21.0, "whoosh_cine", 0.55, None),
    (22.0, "pop_hard", 0.5, None), (23.0, "sweep_small", 0.4, None), (24.0, "drop_water", 0.55, None),
    (25.0, "pop_light", 0.4, None), (25.14, "pop_light", 0.35, None), (25.28, "pop_light", 0.35, None),
    (26.0, "whoosh_fast", 0.5, None), (27.0, "drop_liquid", 0.6, None), (28.0, "whoosh_cine", 0.55, None), (29.0, "sweep_small", 0.5, None),
    (30.0, "click_double", 0.8, None), (31.0, "swoosh_wind", 0.45, None), (32.0, "pop_hard", 0.55, None), (33.0, "sweep_small", 0.45, None),
    (34.0, "click_ui", 0.9, None), (35.0, "click_ui", 0.9, None), (36.0, "whoosh_fast", 0.5, None), (37.0, "click_select", 0.85, None),
    (38.0, "tone_correct", 0.55, 1.2), (39.0, "type_soft", 0.5, 0.9), (40.0, "sweep_small", 0.45, None), (41.0, "tone_success", 0.55, 1.2),
    (42.0, "impact_deep", 0.8, 1.6), (44.0, "swoosh_vacuum", 0.5, 1.2), (46.0, "shutter_lens", 0.6, None), (47.0, "shutter_digital", 0.6, None),
    (48.0, "whoosh_cine", 0.55, None), (49.0, "swoosh_vacuum", 0.5, 1.0), (50.0, "impact_big", 0.6, 1.4),
    (51.0, "pop_light", 0.4, None), (51.12, "pop_light", 0.35, None), (51.24, "pop_light", 0.35, None), (51.36, "pop_light", 0.35, None),
]


def main():
    out = music() * 0.75
    cache = {}
    for beat, name, gain, max_len in EVENTS:
        key = (name, max_len)
        if key not in cache:
            cache[key] = load(os.path.join(SFX, name + ".mp3"), max_len)
        place(out, cache[key], beat * B, gain)
    out = np.tanh(out * 1.1) / np.tanh(1.1)
    raw = os.path.join(ROOT, "build", "mix_raw.wav")
    with wave.open(raw, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
    final = os.path.join(ROOT, "build", "soundtrack.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", str(SR), final], check=True)
    print("ok", final)


if __name__ == "__main__":
    main()
