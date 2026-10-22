"""CamouRoles reel #3 v2 — "Gold Riot". 15 s, 9:16. Punk x luxury.

Black + gold foil + blood red, ransom-note letters, torn tape, stamps, halftone, glitch, hard cuts.
Soundtrack: distorted trap at 150 BPM with vinyl crackle (synthesised here).
Run:  python make_reel4.py  ->  camouroles_reel_03_gold_riot.mp4
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
sys.path.insert(0, HERE)
import make_reel as base  # noqa: E402
import make_reel3 as lux  # noqa: E402  (gold gradient text + light sweep)

from make_reel import W, H, FPS, clamp, ease_out_back, ease_out_cubic, text_img, place, shake  # noqa: E402

OUT = os.path.join(HERE, "camouroles_reel_03_gold_riot.mp4")
WAV = os.path.join(HERE, "soundtrack4.wav")
DUR = 15.0
BPM = 150
B = 60 / BPM

FONTS = "C:/Windows/Fonts/"
F_IMPACT = FONTS + "impact.ttf"
F_CAST = FONTS + "CASTELAR.TTF"
F_BOD = FONTS + "BOD_B.TTF"
F_ROCK = FONTS + "ROCKEB.TTF"
F_COOPER = FONTS + "COPRGTB.TTF"
F_MONO = FONTS + "consolab.ttf"
F_BLACK = FONTS + "seguibl.ttf"
F_ELEPH = FONTS + "ELEPHNT.TTF"
RANSOM_FONTS = [F_IMPACT, F_CAST, F_BOD, F_ROCK, F_COOPER, F_ELEPH, F_BLACK]

INK = (8, 7, 8)
RED = (200, 16, 32)
GOLD = (222, 176, 82)
PAPER = (240, 232, 212)
WHITE = (255, 255, 255)

# scene starts (s): hard cuts
T = {"hook": 0.0, "unlisted": 1.6, "vip": 3.2, "count": 5.6, "agent": 7.6, "yours": 10.0, "end": 11.8}
ORDER = list(T)


def foil(txt, font, size, tracking=0):
    return lux.gold_text(txt, font, size, tracking)


# --------------------------------------------------------------------------- punk pieces
def ransom(word, size=150, seed=0):
    """A word made of cut-out letters: mixed fonts, paper/gold/red/black scraps, tilted."""
    rnd = random.Random(seed)
    tiles = []
    for ch in word:
        if ch == " ":
            tiles.append(None)
            continue
        font = rnd.choice(RANSOM_FONTS)
        bgc, fg = rnd.choice([(PAPER, INK), (GOLD, INK), (RED, WHITE), (INK, GOLD), (WHITE, RED)])
        s = int(size * rnd.uniform(0.85, 1.12))
        t = text_img(ch, font, s, fg)
        pad = rnd.randint(8, 18)
        tile = Image.new("RGBA", (t.width + pad * 2, t.height + pad * 2), bgc + (255,))
        tile.paste(t, (pad, pad), t)
        tile = tile.rotate(rnd.uniform(-9, 9), expand=True, resample=Image.BICUBIC)
        tiles.append(tile)
    w = sum((t.width - 8) if t else size // 3 for t in tiles) + 20
    h = max(t.height for t in tiles if t) + 20
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 10
    for t in tiles:
        if t is None:
            x += size // 3
            continue
        im.paste(t, (x, (h - t.height) // 2 + rnd.randint(-10, 10)), t)
        x += t.width - 8
    if im.width > 960:  # keep long words on screen
        im = im.resize((960, int(im.height * 960 / im.width)), Image.LANCZOS)
    return im


def tape(txt, color=GOLD, ink=INK, size=56, seed=1):
    rnd = random.Random(seed)
    t = text_img(txt, F_IMPACT, size, ink)
    w, h = t.width + 80, t.height + 34
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # jagged short ends like torn tape
    left = [(rnd.randint(0, 12), y) for y in range(0, h + 1, 10)]
    right = [(w - rnd.randint(0, 12), y) for y in range(h, -1, -10)]
    d.polygon(left + right, fill=color + (235,))
    im.paste(t, (40, 17), t)
    return im


def stamp(txt, color=RED, size=110):
    t = text_img(txt, F_IMPACT, size, color)
    w, h = t.width + 60, t.height + 40
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((4, 4, w - 5, h - 5), outline=color + (255,), width=10)
    im.paste(t, (30, 20), t)
    # rough ink: knock random specks out
    a = np.asarray(im).copy()
    rng_ = np.random.default_rng(len(txt))
    holes = rng_.random(a.shape[:2]) < 0.12
    a[holes, 3] = 0
    return Image.fromarray(a)


def scribble_strike(c, x0, x1, y, k, color=RED, seed=2):
    if k <= 0:
        return
    rnd = random.Random(seed)
    d = ImageDraw.Draw(c)
    pts = []
    n = 14
    for i in range(int(n * clamp(k)) + 1):
        pts.append((x0 + (x1 - x0) * i / n, y + rnd.uniform(-22, 22)))
    if len(pts) > 1:
        d.line(pts, fill=color, width=16, joint="curve")


# halftone dots texture (multiplied in faintly)
_ht = Image.new("L", (W, H), 0)
_d = ImageDraw.Draw(_ht)
for yy_ in range(0, H, 14):
    for xx_ in range(0, W, 14):
        r = 2.5 + 2 * math.sin(xx_ / 140) * math.cos(yy_ / 190)
        _d.ellipse((xx_ - r, yy_ - r, xx_ + r, yy_ + r), fill=255)
HALFTONE = np.asarray(_ht, np.float32)[..., None] / 255.0

rng = np.random.default_rng(11)
GRAIN = [rng.normal(0, 9, (H, W, 1)).astype(np.float32) for _ in range(4)]


def glitch_arr(a, amount, seed):
    if amount <= 0:
        return a
    a = a.copy()
    rnd = random.Random(seed)
    for _ in range(int(4 + 22 * amount)):
        y = rnd.randrange(0, H - 10)
        h = rnd.randrange(6, int(20 + 120 * amount))
        a[y:y + h] = np.roll(a[y:y + h], int(rnd.uniform(-1, 1) * 160 * amount), axis=1)
    s = int(3 + 18 * amount)
    out = a.copy()
    out[..., 0] = np.roll(a[..., 0], s, axis=1)
    out[..., 2] = np.roll(a[..., 2], -s, axis=1)
    return out


def slam(u, start=0.0, dur=0.12, big=2.4):
    return 1 + big * (1 - ease_out_cubic((u - start) / dur))


# --------------------------------------------------------------------------- scenes
def s_hook(c, u):
    dx, dy = shake(u, 0.0, 0.16, 26, 1)
    place(c, foil("NOT EVERY JOB", F_IMPACT, 170), W / 2 + dx, 720 + dy, slam(u))
    if u >= 0.55:
        place(c, ransom("IS PUBLIC.", 150, 4), W / 2, 960, ease_out_back((u - 0.55) / 0.15, 2.4), -3)
    if u >= 1.05:
        place(c, tape("sorry, job boards", RED, WHITE, 52, 3), W / 2 + 180, 1190, ease_out_back((u - 1.05) / 0.15), 7)


def s_unlisted(c, u):
    place(c, text_img("THE", F_IMPACT, 90, RED), W / 2, 640, ease_out_back(u / 0.12, 2.2))
    dx, dy = shake(u, 0.12, 0.16, 22, 2)
    im = lux.sweep(foil("UNLISTED", F_CAST, 190), (u - 0.6) / 0.7)
    place(c, im, W / 2 + dx, 830 + dy, slam(u, 0.12, 0.14, 1.8))
    if u >= 0.75:
        st = stamp("CLASSIFIED")
        place(c, st, W / 2 + 40, 1080, 1 + 1.5 * (1 - ease_out_cubic((u - 0.75) / 0.1)), -12)
    if u >= 1.15:
        place(c, tape("VIP ONLY", GOLD, INK, 60, 5), W / 2 - 220, 520, ease_out_back((u - 1.15) / 0.15), -14)


VIP = [("AEROSPACE", 11), ("ROBOTICS", 12), ("QUANT", 13), ("FUSION", 14), ("DEEP TECH", 15)]


def s_vip(c, u):
    i = min(len(VIP) - 1, int(u / 0.48))
    k = u - i * 0.48
    word, seed = VIP[i]
    place(c, text_img(f"{i + 1:02d}", F_MONO, 300, (40, 36, 30)), W / 2, 520)
    if i % 2:
        place(c, foil(word, F_IMPACT, 230 if len(word) < 8 else 180), W / 2, 960, slam(k, 0, 0.1, 1.6), )
    else:
        place(c, ransom(word, 150, seed), W / 2, 960, slam(k, 0, 0.1, 1.4), (-4, 3, -2)[i % 3])
    place(c, tape("hiring", RED if i % 2 else GOLD, WHITE if i % 2 else INK, 46, seed), W / 2 + 230, 1170, 1, 9 - i * 4)
    scribble_strike(c, 180, 900, 1320, (k - 0.15) / 0.25, GOLD, seed)


def s_count(c, u):
    n = int(10000 * ease_out_cubic(u / 0.7))
    dx, dy = shake(u, 0.7, 0.18, 30, 7)
    place(c, lux.sweep(foil(f"{n:,}+", F_IMPACT, 280), (u - 0.8) / 0.6), W / 2 + dx, 820 + dy)
    if u >= 0.85:
        place(c, ransom("VERIFIED.", 120, 21), W / 2, 1060, ease_out_back((u - 0.85) / 0.14, 2.2), 2)
    if u >= 1.3:
        place(c, tape("no fluff. no reposts.", RED, WHITE, 54, 22), W / 2, 1250, ease_out_back((u - 1.3) / 0.15), -5)


LINES = ["> reading your CV...", "> 3 yrs embedded, Pune", "> 37 roles that fit", "> top match: 96%"]


def s_agent(c, u):
    place(c, foil("YOUR AI", F_IMPACT, 150), W / 2, 520, slam(u, 0, 0.1, 1.6))
    place(c, ransom("RECRUITER", 120, 31), W / 2, 700, ease_out_back((u - 0.25) / 0.14, 2.2), -2)
    d = ImageDraw.Draw(c)
    d.rectangle((90, 860, W - 90, 1420), fill=(16, 14, 12), outline=GOLD, width=4)
    for j, line in enumerate(LINES):
        start = 0.55 + j * 0.38
        if u < start:
            break
        n = int(len(line) * clamp((u - start) / 0.25))
        col = GOLD if j < 3 else RED
        t = text_img(line[:n] or " ", F_MONO, 58, col)
        c.paste(t, (130, 900 + j * 120), t)
    if int(u * 6) % 2 == 0:
        d.rectangle((130, 1380, 160, 1400), fill=GOLD)
    if u >= 2.05:
        place(c, stamp("PERSONAL", GOLD, 80), W / 2 + 200, 1530, 1 + 1.4 * (1 - ease_out_cubic((u - 2.05) / 0.1)), 10)


def s_yours(c, u):
    place(c, ransom("WHICH ONE'S", 120, 41), W / 2, 620, ease_out_back(u / 0.14, 2.2), -3)
    dx, dy = shake(u, 0.2, 0.15, 24, 8)
    place(c, foil("YOURS?", F_IMPACT, 300), W / 2 + dx, 860 + dy, slam(u, 0.2, 0.12, 2.0))
    if u >= 0.7:
        place(c, tape("tell us in the comments", GOLD, INK, 54, 42), W / 2, 1120, ease_out_back((u - 0.7) / 0.15), 4)
    if u >= 1.0:
        y = 1330 + 18 * math.sin(u * 16)
        ImageDraw.Draw(c).polygon([(W / 2 - 60, y - 40), (W / 2 + 60, y - 40), (W / 2, y + 40)], fill=RED)


LOGO_IMG = lux.LOGO_IMG


def s_end(c, u):
    # logo slams in with a ring of gold stars
    dx, dy = shake(u, 0.12, 0.2, 28, 9)
    d = ImageDraw.Draw(c)
    for j in range(12):
        ang = j * math.pi / 6 + u * 0.6
        r = 380 * ease_out_cubic(u / 0.4)
        x, y = W / 2 + math.cos(ang) * r, 660 + math.sin(ang) * r
        s = 14
        d.polygon([(x, y - s * 2), (x + s * 0.6, y - s * 0.6), (x + s * 2, y), (x + s * 0.6, y + s * 0.6),
                   (x, y + s * 2), (x - s * 0.6, y + s * 0.6), (x - s * 2, y), (x - s * 0.6, y - s * 0.6)], fill=GOLD)
    place(c, lux.LOGO_GLOW, W / 2, 660, 1.05, 0.4)
    place(c, lux.sweep(LOGO_IMG, (u - 0.5) / 0.8, 0.12), W / 2 + dx, 660 + dy, slam(u, 0, 0.14, 1.2) * 0.95)
    if u >= 0.3:
        place(c, foil("CAMOUROLES", F_IMPACT, 165, 6), W / 2, 1060, slam(u, 0.3, 0.1, 1.2))
    if u >= 0.65:
        place(c, ransom("NO GATEKEEPING.", 82, 51), W / 2, 1220, ease_out_back((u - 0.65) / 0.15, 2.2), -2)
    if u >= 1.0:
        place(c, tape("camouroles.pages.dev", GOLD, INK, 60, 52), W / 2, 1390, ease_out_back((u - 1.0) / 0.15), 3)
    if u >= 1.4:
        place(c, stamp("FOLLOW", RED, 70), W / 2 - 230, 1580, 1 + 1.4 * (1 - ease_out_cubic((u - 1.4) / 0.1)), -10)
        place(c, stamp("SAVE IT", GOLD, 70), W / 2 + 230, 1590, 1 + 1.4 * (1 - ease_out_cubic((u - 1.55) / 0.1)), 9)


SCENES = {"hook": s_hook, "unlisted": s_unlisted, "vip": s_vip, "count": s_count,
          "agent": s_agent, "yours": s_yours, "end": s_end}


def render(t):
    name = [n for n in ORDER if t >= T[n]][-1]
    u = t - T[name]
    c = Image.new("RGB", (W, H), INK)
    # faint gold marquee behind everything
    base.marquee(c, "PRIVATE  ACCESS  PRIVATE  ACCESS", GOLD, 230, t * 380, 110, 0.07)
    base.marquee(c, "PRIVATE  ACCESS  PRIVATE  ACCESS", GOLD, 1780, -t * 380, 110, 0.07)
    SCENES[name](c, u)
    a = np.asarray(c, np.float32)
    a = a * (1 - 0.18 * HALFTONE) + GRAIN[int(t * FPS) % 4]
    # hard cut: white/red flash + glitch for a few frames
    for n in ORDER[1:]:
        dt = t - T[n]
        if 0 <= dt < 0.1:
            flash = np.array(WHITE if ORDER.index(n) % 2 else RED, np.float32)
            a = a + (flash - a) * (0.6 * (1 - dt / 0.1))
            a = glitch_arr(np.clip(a, 0, 255), 0.6 * (1 - dt / 0.1), int(t * 1000))
    return np.clip(a, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- soundtrack: dark distorted trap
SR = 44100
N = int(SR * DUR)
add, env_exp, noise, hp = base.add, base.env_exp, base.noise, base.hp


def dist808(f, length, glide=None):
    n = int(length * SR)
    tt = np.arange(n) / SR
    fr = np.full(n, f) if glide is None else f * (glide / f) ** np.minimum(1, tt / 0.1)
    x = np.sin(2 * np.pi * np.cumsum(fr) / SR)
    click = np.sin(2 * np.pi * np.cumsum(70 + 160 * np.exp(-tt * 45)) / SR) * np.exp(-tt * 30)
    return np.tanh(4.0 * (x * env_exp(n, 0.45) + click)) * 0.8


def snare_hard(seed):
    n = int(0.3 * SR)
    tt = np.arange(n) / SR
    return np.tanh(3 * (hp(noise(n, seed)) * env_exp(n, 0.09) + np.sin(2 * np.pi * 180 * tt) * np.exp(-tt * 30))) * 0.7


def crackle():
    x = np.zeros(N)
    r = np.random.default_rng(5)
    idx = r.integers(0, N, 900)
    x[idx] = r.uniform(-1, 1, 900)
    return np.convolve(x, np.exp(-np.arange(60) / 8), "same") * 0.12 + r.normal(0, 0.004, N)


def braam(length=1.2):
    n = int(length * SR)
    tt = np.arange(n) / SR
    x = sum(np.sign(np.sin(2 * np.pi * f * tt)) for f in (55, 55.4, 82.4, 110.3)) / 4
    return np.tanh(2 * x) * env_exp(n, 0.5) * np.minimum(1, tt / 0.01)


def build_audio():
    L = crackle()
    roots = [36.7, 36.7, 43.65, 32.7]  # D1 D1 F1 C1
    beat, t = 0, 0.0
    while t < DUR - 1.4:
        bar, pos = beat // 4, beat % 4
        if pos == 0 or (pos == 2 and bar % 2) or (pos == 3 and bar % 2 == 0):
            gl = roots[(bar + 1) % 4] * 2 if pos == 3 else None
            add(L, t, dist808(roots[bar % 4] * 2, B * 1.5, gl), 0.6)
        if pos == 2:
            add(L, t, snare_hard(beat), 0.65)
        rolls = 6 if bar % 4 == 3 else 2
        for h in range(rolls):
            add(L, t + h * B / rolls, base.hat(beat * 6 + h, 0.025), 0.5)
        beat += 1
        t += B
    for n in ORDER:
        add(L, T[n], braam(0.9), 0.35)  # a heavy brass hit on every cut
    add(L, T["unlisted"] + 0.75, braam(0.6), 0.3)  # CLASSIFIED stamp
    for j in range(len(LINES)):  # terminal typing
        for i in range(10):
            add(L, T["agent"] + 0.55 + j * 0.38 + i * 0.025, base.hat(700 + j * 10 + i, 0.015), 0.6)
    end0 = T["end"]
    L[int((end0 - 0.08) * SR):int(end0 * SR)] *= 0.1
    add(L, end0, dist808(73.4, 2.5), 0.8)
    add(L, end0, braam(2.0), 0.45)
    R = np.roll(L, int(0.011 * SR)) * 0.95
    st = np.stack([L, R], 1)
    st = np.tanh(st * 1.3) / np.tanh(1.3)
    fade = np.ones(N)
    fade[-int(0.5 * SR):] = np.linspace(1, 0, int(0.5 * SR))
    st *= fade[:, None] * 0.9
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
    for i in range(int(DUR * FPS)):
        proc.stdin.write(render(i / FPS).tobytes())
        if i % 90 == 0:
            print(f"frame {i}", flush=True)
    proc.stdin.close()
    proc.wait()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-c:v", "libx264", "-preset", "slow", "-crf", "22",
                    "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", OUT], check=True)
    os.remove(raw)
    print("done:", OUT)


if __name__ == "__main__":
    main()
