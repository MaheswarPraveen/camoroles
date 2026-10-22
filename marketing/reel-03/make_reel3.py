"""CamouRoles reel #3 — "Private Collection". 15 s, 9:16, luxury style.

Black/maroon, gold-gradient serif type, light sweeps, gold dust, slow push-ins, crossfades.
Soundtrack: piano + string pad + heartbeat bass + shimmer hits (all synthesised here).
Run:  python make_reel3.py   ->  camouroles_reel_03_private.mp4
"""
import math
import os
import random
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "reel-01"))
import make_reel as base  # noqa: E402  (easing + audio helpers)

from make_reel import W, H, FPS, clamp, ease_out_cubic, ease_in_out  # noqa: E402

OUT = os.path.join(HERE, "camouroles_reel_03_private.mp4")
WAV = os.path.join(HERE, "soundtrack3.wav")
LOGO = os.path.join(HERE, "..", "..", "static", "logo-gold.png")
DUR = 15.0

FONTS = "C:/Windows/Fonts/"
F_BODONI = FONTS + "BOD_R.TTF"
F_BODONI_I = FONTS + "BOD_I.TTF"
F_CASTELLAR = FONTS + "CASTELAR.TTF"
F_COPPER = FONTS + "COPRGTL.TTF"
F_GARA_I = FONTS + "GARAIT.TTF"

CREAM = (244, 233, 214)
GOLD_DARK, GOLD_MID, GOLD_LIGHT = (150, 104, 38), (214, 168, 84), (255, 232, 170)
MAROON = (58, 10, 22)

# scene start times (s)
T = {"line": 0.0, "card": 2.6, "list": 5.0, "count": 7.6, "agent": 9.8, "end": 12.2}
FADE = 0.45


# --------------------------------------------------------------------------- backgrounds and texture
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def radial_bg(cx, cy, inner, outer, radius):
    d = np.sqrt(((xx - cx) / W) ** 2 + ((yy - cy) / H) ** 2) / radius
    k = np.clip(d, 0, 1)[..., None]
    return (np.array(inner, np.float32) * (1 - k) + np.array(outer, np.float32) * k)


BG = radial_bg(W / 2, H * 0.42, (70, 14, 28), (6, 4, 6), 0.75)
rng = np.random.default_rng(3)
GRAIN = [rng.normal(0, 4.5, (H, W, 1)).astype(np.float32) for _ in range(4)]

DUST = [(random.Random(i).uniform(0, W), random.Random(i + 1).uniform(0, H), random.Random(i + 2).uniform(1.5, 4.5),
         random.Random(i + 3).uniform(0, 6.28), random.Random(i + 4).uniform(10, 40)) for i in range(110)]


def draw_dust(img, t):
    d = ImageDraw.Draw(img, "RGBA")
    for x, y, r, ph, sp in DUST:
        yy_ = (y - t * sp) % H
        xx_ = x + 14 * math.sin(t * 0.6 + ph)
        a = int(140 * (0.5 + 0.5 * math.sin(t * 2.2 + ph)))
        d.ellipse((xx_ - r, yy_ - r, xx_ + r, yy_ + r), fill=(255, 220, 150, a))


# --------------------------------------------------------------------------- gold type
_cache = {}


def gold_text(txt, font, size, tracking=0, color=None):
    """Text filled with a vertical gold gradient (or a flat colour). Returns RGBA."""
    key = (txt, font, size, tracking, color)
    if key in _cache:
        return _cache[key]
    f = ImageFont.truetype(font, size)
    if tracking:
        widths = [f.getbbox(ch)[2] if ch != " " else size * 0.3 for ch in txt]
        w = int(sum(widths) + tracking * (len(txt) - 1)) + 40
    else:
        w = f.getbbox(txt)[2] + 40
    h = int(size * 1.45)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    if tracking:
        x = 20
        for ch, cw in zip(txt, widths):
            d.text((x, size * 0.15), ch, font=f, fill=255)
            x += cw + tracking
    else:
        d.text((20, size * 0.15), txt, font=f, fill=255)
    if color:
        fill = Image.new("RGB", (w, h), color)
    else:
        g = np.linspace(0, 1, h)[:, None]
        stops = np.array([GOLD_LIGHT, GOLD_MID, GOLD_DARK, GOLD_MID], np.float32)
        pos = np.array([0, 0.35, 0.62, 1.0])
        col = np.stack([np.interp(g[:, 0], pos, stops[:, c]) for c in range(3)], 1)
        fill = Image.fromarray(np.repeat(col[:, None, :], w, 1).astype(np.uint8))
    im = fill.convert("RGBA")
    im.putalpha(mask)
    _cache[key] = im
    return im


def sweep(im, k, width=0.18):
    """Diagonal light band crossing the text. k 0..1 = band position."""
    if not 0 < k < 1:
        return im
    w, h = im.size
    a = np.asarray(im).astype(np.float32)
    pos = (np.arange(w)[None, :] + np.arange(h)[:, None] * 0.6) / (w + h * 0.6)
    band = np.clip(1 - np.abs(pos - (k * 1.4 - 0.2)) / width, 0, 1) ** 2
    a[..., :3] = a[..., :3] + (255 - a[..., :3]) * band[..., None] * 0.85
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def place(c, im, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.01:
        return
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if alpha < 0.999:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    c.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


def rise(k, dist=40):
    """Fade + small upward drift for a reveal; returns (alpha, dy)."""
    e = ease_out_cubic(k)
    return clamp(k * 1.4), dist * (1 - e)


def gold_line(c, cx, cy, half, k, thick=3):
    if k <= 0:
        return
    h = half * ease_in_out(k)
    d = ImageDraw.Draw(c)
    d.line((cx - h, cy, cx + h, cy), fill=GOLD_MID, width=thick)
    d.ellipse((cx - h - 5, cy - 5, cx - h + 5, cy + 5), fill=GOLD_LIGHT)
    d.ellipse((cx + h - 5, cy - 5, cx + h + 5, cy + 5), fill=GOLD_LIGHT)


# --------------------------------------------------------------------------- scenes (u = local time)
def scene_line(c, u):
    gold_line(c, W / 2, 960, 380, u / 0.9)
    a, dy = rise((u - 0.45) / 0.7)
    place(c, gold_text("Not every opportunity", F_BODONI, 84, color=CREAM), W / 2, 860 + dy, 1, a)
    a, dy = rise((u - 1.05) / 0.7)
    place(c, sweep(gold_text("is listed publicly.", F_BODONI_I, 96), (u - 1.6) / 0.8), W / 2, 1070 + dy, 1, a)


def emboss_card():
    w, h = 860, 640
    im = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    shadow = Image.new("L", im.size, 0)
    ImageDraw.Draw(shadow).rounded_rectangle((50, 60, w + 40, h + 50), 40, fill=170)
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))
    im.paste((0, 0, 0, 255), (0, 0), shadow)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((40, 40, w + 40, h + 40), 40, fill=(44, 8, 18), outline=GOLD_MID, width=3)
    d.rounded_rectangle((62, 62, w + 18, h + 18), 30, outline=(150, 104, 38, 180), width=1)
    return im


CARD = emboss_card()


def scene_card(c, u):
    s = 0.96 + 0.05 * ease_in_out(u / 2.4)  # slow push-in
    a, dy = rise(u / 0.6, 60)
    place(c, CARD, W / 2, 960 + dy, s, a)
    a2, _ = rise((u - 0.35) / 0.6)
    place(c, gold_text("THE", F_COPPER, 46, tracking=28), W / 2, 790 + dy, s, a2)
    place(c, sweep(gold_text("UNLISTED", F_CASTELLAR, 150), (u - 1.0) / 1.0), W / 2, 950 + dy, s, a2)
    gold_line(c, W / 2, 1090 + dy, 220 * s, (u - 0.6) / 0.6, 2)
    a3, _ = rise((u - 0.9) / 0.6)
    place(c, gold_text("careers beyond the job boards", F_GARA_I, 60, color=CREAM), W / 2, 1160 + dy, s, a3)


COLLECTION = ["AEROSPACE", "ROBOTICS", "QUANTITATIVE FINANCE", "FUSION ENERGY", "DEEP TECH"]


def scene_list(c, u):
    a, dy = rise(u / 0.6)
    place(c, gold_text("the collection", F_BODONI_I, 92), W / 2, 560 + dy, 1, a)
    gold_line(c, W / 2, 650, 160, (u - 0.2) / 0.5, 2)
    for j, item in enumerate(COLLECTION):
        k = (u - 0.45 - j * 0.28) / 0.55
        a, dy = rise(k, 30)
        y = 790 + j * 150
        place(c, gold_text(item, F_COPPER, 58, tracking=10, color=CREAM), W / 2, y + dy, 1, a)
        if j < len(COLLECTION) - 1 and k > 0.3:
            ImageDraw.Draw(c).ellipse((W / 2 - 5, y + 70, W / 2 + 5, y + 80), fill=GOLD_MID)


def scene_count(c, u):
    n = int(10000 * ease_out_cubic(u / 1.1))
    a, dy = rise(u / 0.5)
    place(c, sweep(gold_text(f"{n:,}+", F_BODONI, 230), (u - 1.1) / 0.8), W / 2, 830 + dy, 1, a)
    a, dy = rise((u - 0.8) / 0.6)
    place(c, gold_text("verified openings.", F_BODONI_I, 84, color=CREAM), W / 2, 1040 + dy, 1, a)
    gold_line(c, W / 2, 1150, 150, (u - 1.0) / 0.5, 2)
    a, dy = rise((u - 1.2) / 0.6)
    place(c, gold_text("DIRECT FROM THE SOURCE", F_COPPER, 46, tracking=12), W / 2, 1230 + dy, 1, a)


def scene_agent(c, u):
    a, dy = rise(u / 0.6)
    place(c, gold_text("Your personal", F_BODONI_I, 84, color=CREAM), W / 2, 760 + dy, 1, a)
    a, dy = rise((u - 0.35) / 0.6)
    place(c, sweep(gold_text("AI RECRUITER", F_CASTELLAR, 116), (u - 0.9) / 0.9), W / 2, 920 + dy, 1, a)
    gold_line(c, W / 2, 1040, 260, (u - 0.6) / 0.6, 2)
    a, dy = rise((u - 1.0) / 0.6)
    place(c, gold_text("reads your CV.", F_GARA_I, 80, color=CREAM), W / 2, 1130 + dy, 1, a)
    a, dy = rise((u - 1.35) / 0.6)
    place(c, gold_text("finds your fit.", F_GARA_I, 80, color=CREAM), W / 2, 1235 + dy, 1, a)


LOGO_IMG = Image.open(LOGO).convert("RGBA")
LOGO_IMG = LOGO_IMG.resize((int(LOGO_IMG.width * 520 / LOGO_IMG.height), 520), Image.LANCZOS)
LOGO_GLOW = LOGO_IMG.filter(ImageFilter.GaussianBlur(50))


def url_box():
    t = gold_text("camouroles.pages.dev", F_COPPER, 42, tracking=6, color=CREAM)
    im = Image.new("RGBA", (t.width + 80, t.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle((2, 2, im.width - 3, im.height - 3), outline=GOLD_MID, width=2)
    im.paste(t, (40, 20), t)
    return im


URL_BOX = url_box()


def scene_end(c, u):
    # vertical light column the logo rises out of
    col_a = clamp(u / 0.5) * (1 - clamp((u - 1.3) / 0.8))
    if col_a > 0:
        g = np.exp(-((np.arange(W) - W / 2) / 120.0) ** 2)
        band = Image.fromarray((np.repeat(g[None, :], H, 0) * 120 * col_a).astype(np.uint8))
        c.paste((255, 220, 150), (0, 0), band)
    a, dy = rise((u - 0.15) / 0.9, 120)
    place(c, LOGO_GLOW, W / 2, 680 + dy, 1.05, 0.5 * a)
    place(c, sweep(LOGO_IMG, (u - 1.0) / 1.0, 0.12), W / 2, 680 + dy, 1, a)
    a, dy = rise((u - 0.8) / 0.7)
    place(c, gold_text("CAMOUROLES", F_COPPER, 82, tracking=22), W / 2, 1060 + dy, 1, a)
    gold_line(c, W / 2, 1150, 200, (u - 1.0) / 0.6, 2)
    a, dy = rise((u - 1.25) / 0.7)
    place(c, gold_text("The private collection", F_BODONI_I, 64, color=CREAM), W / 2, 1230 + dy, 1, a)
    place(c, gold_text("of niche careers", F_BODONI_I, 64, color=CREAM), W / 2, 1305 + dy, 1, a)
    a, dy = rise((u - 1.7) / 0.7)
    place(c, URL_BOX, W / 2, 1450 + dy, 1, a)


SCENES = [("line", scene_line), ("card", scene_card), ("list", scene_list),
          ("count", scene_count), ("agent", scene_agent), ("end", scene_end)]


def scene_alpha(name, t):
    """Each scene fades in over FADE and out over FADE before the next starts."""
    keys = [k for k, _ in SCENES]
    i = keys.index(name)
    start = T[name]
    end = T[keys[i + 1]] if i + 1 < len(keys) else DUR
    if t < start or t > end + FADE * 0.5:
        return 0.0
    a_in = 1.0 if i == 0 else clamp((t - start) / FADE)
    a_out = clamp((end - t) / FADE + 0.15) if i + 1 < len(keys) else clamp((DUR - t) / 0.5)
    return min(a_in, a_out)


def render(t):
    base_img = BG.copy()
    out = Image.fromarray(base_img.astype(np.uint8))
    draw_dust(out, t)
    for name, fn in SCENES:
        a = scene_alpha(name, t)
        if a <= 0:
            continue
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fn(layer, t - T[name])
        if a < 1:
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
        out.paste(layer, (0, 0), layer)
    arr = np.asarray(out, np.float32) + GRAIN[int(t * FPS) % 4]
    return np.clip(arr, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- soundtrack
SR = 44100
N = int(SR * DUR)
add, env_exp, noise, hp = base.add, base.env_exp, base.noise, base.hp


def pad(freqs, length, attack=1.2):
    n = int(length * SR)
    tt = np.arange(n) / SR
    x = np.zeros(n)
    for f in freqs:
        for det in (-0.6, 0.0, 0.6):  # three detuned voices = a soft string section
            ph = random.Random(int(f * 10 + det * 7)).uniform(0, 6.28)
            x += np.sin(2 * np.pi * (f + det) * tt + ph) + 0.3 * np.sin(4 * np.pi * (f + det) * tt + ph)
    env = np.minimum(1, tt / attack) * np.minimum(1, (length - tt) / 1.0).clip(0, 1)
    return x / (len(freqs) * 3) * env


def piano(f, length=2.5):
    n = int(length * SR)
    tt = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * f * k * tt) * np.exp(-tt * (1.2 + k * 0.9)) for k, a in ((1, 1), (2, 0.45), (3, 0.2), (4, 0.1)))
    return x * np.minimum(1, tt / 0.004)


def heartbeat():
    def thump(freq):
        n = int(0.35 * SR)
        tt = np.arange(n) / SR
        return np.sin(2 * np.pi * np.cumsum(freq + 40 * np.exp(-tt * 30)) / SR) * np.exp(-tt * 14)
    x = np.zeros(int(0.7 * SR))
    a = thump(52)
    x[:len(a)] += a
    b = thump(46) * 0.7
    i = int(0.24 * SR)
    x[i:i + len(b)] += b[: len(x) - i]
    return x


def shimmer():
    n = int(2.5 * SR)
    tt = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * tt) for f in (2093, 2637, 3136, 4186)) / 4
    return x * np.exp(-tt * 1.6) * np.minimum(1, tt / 0.01) * 0.5


def reverb(x):
    y = x.copy()
    for d, g in ((0.031, 0.5), (0.067, 0.4), (0.113, 0.32), (0.171, 0.25), (0.263, 0.18), (0.397, 0.12)):
        k = int(d * SR)
        y[k:] += x[:-k] * g
    return y


def build_audio():
    L = np.zeros(N)
    # D minor: Dm - Bb - Gm - A, one chord per scene-ish
    chords = [(146.8, 220.0, 293.7, 349.2), (116.5, 233.1, 293.7, 349.2), (98.0, 196.0, 293.7, 233.1), (110.0, 220.0, 277.2, 329.6)]
    for j, start in enumerate([0.0, 3.7, 7.4, 11.1]):
        add(L, start, pad(chords[j], 4.4 if j < 3 else 3.9), 0.35)
    # piano motif on the reveals
    motif = [(0.5, 587.3), (1.05, 698.5), (1.6, 880.0), (2.95, 587.3), (3.6, 932.3), (5.2, 784.0), (5.5, 698.5),
             (5.8, 587.3), (6.1, 523.3), (6.4, 587.3), (8.1, 880.0), (8.9, 1046.5), (10.1, 698.5), (10.5, 880.0),
             (11.0, 1174.7), (12.5, 587.3), (12.5, 880.0), (12.5, 1174.7), (13.4, 1396.9)]
    for t, f in motif:
        add(L, t, piano(f), 0.22)
    # heartbeat bass, slow and steady
    t = 0.2
    while t < DUR - 1.0:
        add(L, t, heartbeat(), 0.55)
        t += 1.25
    for start in T.values():
        add(L, start + 0.05, shimmer(), 0.25)
    add(L, T["end"], piano(146.8, 3.5), 0.4)  # low D under the logo
    L = reverb(L)
    R = np.roll(L, int(0.015 * SR)) * 0.95
    st = np.stack([L, R], 1)
    st /= np.abs(st).max() + 1e-9
    fade = np.ones(N)
    fade[-int(0.8 * SR):] = np.linspace(1, 0, int(0.8 * SR))
    st *= fade[:, None] * 0.85
    with wave.open(WAV, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def main():
    build_audio()
    raw = OUT.replace(".mp4", "_raw.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", WAV, "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", raw]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frames = int(DUR * FPS)
    for i in range(frames):
        proc.stdin.write(render(i / FPS).tobytes())
        if i % 90 == 0:
            print(f"frame {i}/{frames}", flush=True)
    proc.stdin.close()
    proc.wait()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-c:v", "libx264", "-preset", "slow", "-crf", "21",
                    "-maxrate", "10M", "-bufsize", "20M", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", OUT], check=True)
    os.remove(raw)
    print("done:", OUT)


if __name__ == "__main__":
    main()
