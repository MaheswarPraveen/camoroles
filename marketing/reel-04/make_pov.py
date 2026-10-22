"""CamouRoles reel #4 — "POV: 9 to 5 -> rocket". 15 s, 9:16 story reel.

First-person story: grey Monday at a desk -> phone buzzes with a CamouRoles match -> one apply ->
"6 months later" -> mission control countdown and launch -> end card.
Captions are the character's thoughts (TikTok-style). Soundtrack is synthesised here.
Run:  python make_pov.py  ->  camouroles_reel_04_pov.mp4
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
import make_reel as base  # noqa: E402

from make_reel import W, H, FPS, clamp, ease_out_back, ease_out_cubic, ease_in_out, text_img, place  # noqa: E402

OUT = os.path.join(HERE, "camouroles_reel_04_pov.mp4")
WAV = os.path.join(HERE, "soundtrack_pov.wav")
LOGO = os.path.join(HERE, "..", "..", "static", "logo-gold.png")
DUR = 15.0

FONTS = "C:/Windows/Fonts/"
F_UI = FONTS + "segoeuib.ttf"
F_UI_R = FONTS + "segoeui.ttf"
F_BLACK = FONTS + "seguibl.ttf"
F_MONO = FONTS + "consolab.ttf"
F_SERIF_I = FONTS + "BOD_I.TTF"

# story beats (seconds)
T_OFFICE, T_BUZZ, T_PHONE, T_LATER, T_MISSION, T_END = 0.0, 3.2, 5.4, 8.2, 9.2, 12.8


def ease_in(x):
    x = clamp(x)
    return x * x * x


# --------------------------------------------------------------------------- captions (the character's thoughts)
def caption(c, txt, y, k, size=64):
    if k <= 0:
        return
    t = text_img(txt, F_BLACK, size, (255, 255, 255))
    pad_x, pad_y = 34, 18
    box = Image.new("RGBA", (t.width + pad_x * 2, t.height + pad_y * 2), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle((0, 0, box.width - 1, box.height - 1), 26, fill=(0, 0, 0, 200))
    box.paste(t, (pad_x, pad_y), t)
    place(c, box, W / 2, y, ease_out_back(k / 0.18, 2.0))


# --------------------------------------------------------------------------- scene 1: grey office, 9:00
def office_frame(t):
    c = Image.new("RGB", (W, H), (120, 122, 126))
    d = ImageDraw.Draw(c)
    for y in range(0, 1200, 4):  # wall gradient
        g = int(150 - y * 0.03)
        d.line((0, y, W, y), fill=(g, g + 2, g + 6))
    for y in range(140, 760, 34):  # window blinds, left
        d.rectangle((40, y, 300, y + 20), fill=(178, 182, 188))
    d.rectangle((36, 136, 304, 764), outline=(96, 98, 104), width=8)
    # wall clock, 9:00 with a ticking second hand
    cx, cy, r = 870, 260, 120
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(232, 232, 236), outline=(70, 70, 76), width=10)
    for i in range(12):
        a = i * math.pi / 6
        d.line((cx + math.cos(a) * 92, cy + math.sin(a) * 92, cx + math.cos(a) * 106, cy + math.sin(a) * 106), fill=(60, 60, 66), width=6)
    d.line((cx, cy, cx, cy - 80), fill=(40, 40, 46), width=10)            # 12
    d.line((cx, cy, cx - 70, cy), fill=(40, 40, 46), width=12)            # 9
    sa = -math.pi / 2 + int(t) * math.pi / 30
    d.line((cx, cy, cx + math.cos(sa) * 100, cy + math.sin(sa) * 100), fill=(190, 40, 40), width=4)
    # desk
    d.rectangle((0, 1200, W, H), fill=(92, 88, 84))
    d.rectangle((0, 1190, W, 1214), fill=(70, 66, 62))
    # monitor with an endless spreadsheet
    d.rectangle((520, 1060, 560, 1200), fill=(50, 50, 54))
    d.rectangle((380, 1180, 700, 1206), fill=(50, 50, 54))
    d.rounded_rectangle((150, 470, 930, 1080), 18, fill=(36, 36, 40))
    d.rectangle((180, 500, 900, 1050), fill=(236, 238, 240))
    d.rectangle((180, 500, 900, 540), fill=(64, 140, 90))
    for gx in range(180, 901, 90):
        d.line((gx, 540, gx, 1050), fill=(200, 202, 206), width=2)
    for gy in range(540, 1051, 34):
        d.line((180, gy, 900, gy), fill=(200, 202, 206), width=2)
    sel = int(t * 3) % 14
    d.rectangle((270, 540 + sel * 34, 360, 574 + sel * 34), outline=(40, 120, 220), width=4)
    # keyboard + mug
    d.rounded_rectangle((260, 1300, 820, 1420), 14, fill=(70, 70, 74))
    for ky in range(1318, 1410, 30):
        for kx in range(280, 800, 40):
            d.rectangle((kx, ky, kx + 30, ky + 22), fill=(100, 100, 106))
    d.rounded_rectangle((860, 1280, 980, 1440), 16, fill=(210, 210, 214))
    d.arc((950, 1310, 1030, 1400), -80, 80, fill=(210, 210, 214), width=16)
    return c


def grey_grade(img, amount):
    """Desaturate towards dull grey."""
    a = np.asarray(img, np.float32)
    g = a.mean(axis=2, keepdims=True)
    return Image.fromarray((a * (1 - amount) + g * amount).astype(np.uint8))


def zoom(img, s, cx=W / 2, cy=H / 2):
    w, h = W / s, H / s
    return img.transform((W, H), Image.EXTENT, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), Image.BILINEAR)


# --------------------------------------------------------------------------- scene 2: phone buzzes on the desk
def phone_img(lit, banner_k, t):
    w, h = 420, 820
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 26, w + 20, h + 26), 60, fill=(0, 0, 0, 120))
    d.rounded_rectangle((0, 0, w, h), 60, fill=(22, 22, 26))
    scr = (24, 50, w - 24, h - 40)
    d.rounded_rectangle(scr, 40, fill=(40, 42, 70) if lit else (12, 12, 14))
    if lit:
        d.text((w / 2 - 70, 120), "9:41", font=ImageFont.truetype(F_UI_R, 72), fill=(255, 255, 255))
        if banner_k > 0:
            by = 260 + 60 * (1 - ease_out_back(banner_k / 0.25, 1.4))
            d.rounded_rectangle((40, by, w - 40, by + 190), 30, fill=(250, 250, 252))
            d.rounded_rectangle((60, by + 22, 110, by + 72), 12, fill=(232, 190, 92))
            d.text((124, by + 24), "CamouRoles", font=ImageFont.truetype(F_UI, 30), fill=(30, 30, 34))
            d.text((60, by + 86), "3 roles fit you", font=ImageFont.truetype(F_BLACK, 34), fill=(20, 20, 24))
            d.text((60, by + 130), "Flight Software Eng…", font=ImageFont.truetype(F_UI_R, 30), fill=(90, 90, 96))
    return im


def scene_buzz(u):
    bg = grey_grade(office_frame(T_BUZZ + u), 0.7)
    bg = zoom(bg, 1.12 + 0.1 * ease_in_out(u / 2.2), W / 2, 1300)
    c = bg.copy()
    lit = u >= 0.25
    buzz = (math.sin(u * 90) * 10) if 0.25 <= u < 1.0 else 0
    ph = phone_img(lit, u - 0.35, u)
    place(c, ph.rotate(-8 + buzz * 0.2, expand=True, resample=Image.BICUBIC), W / 2 + buzz, 1240, 1.0 + 0.25 * ease_in_out((u - 1.2) / 1.0))
    caption(c, "wait… what's this", 1650, u - 0.9)
    return c


# --------------------------------------------------------------------------- scene 3: the phone screen (AI chat, one apply)
def bubble(txt, mine, size=50):
    t = text_img(txt, F_UI, size, (255, 255, 255) if mine else (20, 20, 24))
    w, h = t.width + 60, t.height + 40
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), 34, fill=(60, 110, 255) if mine else (238, 238, 242))
    im.paste(t, (30, 20), t)
    return im


def scene_phone(u):
    c = Image.new("RGB", (W, H), (248, 248, 250))
    d = ImageDraw.Draw(c)
    d.rectangle((0, 0, W, 230), fill=(255, 255, 255))
    d.line((0, 230, W, 230), fill=(225, 225, 230), width=3)
    d.rounded_rectangle((60, 90, 150, 180), 20, fill=(232, 190, 92))
    d.text((180, 96), "CamouRoles AI", font=ImageFont.truetype(F_BLACK, 52), fill=(20, 20, 24))
    d.text((180, 160), "your job agent", font=ImageFont.truetype(F_UI_R, 34), fill=(120, 120, 128))
    ask = "I code + love space. 2 yrs exp"
    if u >= 0.15:
        n = int(len(ask) * clamp((u - 0.15) / 0.5))
        b = bubble(ask[:n] or " ", True)
        c.paste(b, (W - 60 - b.width, 320), b)
    if u >= 0.85:
        b = bubble("Found 3 that fit you", False)
        place(c, b, 60 + b.width / 2, 520, ease_out_back((u - 0.85) / 0.18))
    if u >= 1.1:  # job card
        k = u - 1.1
        card = Image.new("RGBA", (W - 120, 330), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, card.width - 1, 329), 36, fill=(255, 255, 255), outline=(225, 225, 232), width=3)
        cd.rounded_rectangle((36, 36, 136, 136), 24, fill=(20, 24, 60))
        cd.text((60, 52), "🚀" if False else "S", font=ImageFont.truetype(F_BLACK, 60), fill=(255, 255, 255))
        cd.text((166, 34), "Flight Software Engineer", font=ImageFont.truetype(F_BLACK, 50), fill=(20, 20, 24))
        cd.text((166, 100), "Satellite startup · Bengaluru", font=ImageFont.truetype(F_UI_R, 38), fill=(110, 110, 118))
        cd.rounded_rectangle((36, 196, 260, 260), 32, fill=(220, 250, 230))
        cd.text((62, 204), "94% fit", font=ImageFont.truetype(F_BLACK, 40), fill=(20, 130, 70))
        pressed = u >= 1.85
        bx0 = card.width - 300
        cd.rounded_rectangle((bx0, 190, card.width - 36, 270), 40, fill=(30, 160, 90) if pressed else (60, 110, 255))
        cd.text((bx0 + (54 if not pressed else 34), 202), "Apply" if not pressed else "Applied", font=ImageFont.truetype(F_BLACK, 44), fill=(255, 255, 255))
        place(c, card, W / 2, 800 + 120 * (1 - ease_out_back(k / 0.25, 1.3)), 0.97 if 1.75 <= u < 1.85 else 1)
    if 1.7 <= u < 1.95:  # finger tap ripple
        k = (u - 1.7) / 0.25
        r = 30 + 90 * k
        ImageDraw.Draw(c, "RGBA").ellipse((W - 210 - r, 1030 - r, W - 210 + r, 1030 + r), outline=(60, 110, 255, int(200 * (1 - k))), width=10)
    caption(c, "ok. one apply. why not.", 1500, u - 2.0)
    return c


# --------------------------------------------------------------------------- "6 months later"
MONTHS = ["MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP"]


def scene_later(u):
    c = Image.new("RGB", (W, H), (6, 6, 10))
    i = min(len(MONTHS) - 1, int(u / 0.09))
    place(c, text_img(MONTHS[i], F_BLACK, 220, (60, 60, 70)), W / 2, 820)
    if u >= 0.35:
        place(c, text_img("6 months later", F_SERIF_I, 120, (240, 240, 245)), W / 2, 1000, 1, )
    return c


# --------------------------------------------------------------------------- scene 4: mission control
STARS = [(random.Random(i).uniform(110, 970), random.Random(i + 5).uniform(330, 860)) for i in range(60)]


def mission(u):
    launch = u >= 2.6
    flash = clamp(1 - (u - 2.6) / 0.6) if launch else 0
    room = (10, 16, 34)
    c = Image.new("RGB", (W, H), room)
    d = ImageDraw.Draw(c)
    # big wall screen
    d.rectangle((70, 290, 1010, 900), fill=(4, 10, 24), outline=(40, 90, 170), width=6)
    for x, y in STARS:
        d.point((x, y), fill=(120, 160, 220))
    # earth limb + trajectory drawing itself
    d.arc((-300, 700, 1380, 1900), 200, 340, fill=(60, 140, 255), width=6)
    k = ease_in_out(u / 2.4)
    pts = [(160 + 760 * s, 820 - 420 * math.sin(s * math.pi / 2) ** 0.8) for s in np.linspace(0, k, 40)]
    if len(pts) > 1:
        d.line(pts, fill=(255, 200, 80), width=6)
        x, y = pts[-1]
        d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=(255, 220, 120))
    # countdown
    count = max(0, 10 - int(u / 0.25))
    label = f"T-{count:02d}" if not launch else "LIFTOFF"
    col = (255, 255, 255) if not launch else (255, 200, 80)
    place(c, text_img(label, F_MONO, 120 if not launch else 110, col), W / 2, 400)
    # side status panels
    for j, (lbl, ok) in enumerate((("FUEL", True), ("GNC", True), ("COMMS", True), ("WEATHER", u > 1.2))):
        y = 980 + j * 60
        d.text((110, y), lbl, font=ImageFont.truetype(F_MONO, 40), fill=(140, 170, 220))
        d.text((420, y), "GO" if ok else "HOLD", font=ImageFont.truetype(F_MONO, 40), fill=(80, 230, 140) if ok else (255, 170, 60))
    # consoles in the foreground + colleagues' silhouettes
    d.rectangle((0, 1300, W, H), fill=(14, 18, 30))
    for j, cx in enumerate((220, 860)):
        d.ellipse((cx - 90, 1130, cx + 90, 1310), fill=(4, 6, 12))
        d.rounded_rectangle((cx - 170, 1270, cx + 170, 1420), 70, fill=(4, 6, 12))
        d.arc((cx - 110, 1110, cx + 110, 1310), 200, 340, fill=(30, 30, 40), width=12)  # headset
    for j in range(18):
        x = 60 + j * 56
        on = (int(u * 8) + j) % 3 == 0
        d.ellipse((x, 1480, x + 22, 1502), fill=(80, 230, 140) if on else (40, 60, 50))
    # my own console screen (first person) with my name tag
    d.rounded_rectangle((300, 1560, 780, 1840), 20, fill=(10, 30, 60), outline=(60, 140, 255), width=4)
    d.text((340, 1600), "FLIGHT SOFTWARE", font=ImageFont.truetype(F_MONO, 40), fill=(140, 190, 255))
    d.text((340, 1660), "STATUS: GO", font=ImageFont.truetype(F_MONO, 46), fill=(80, 230, 140))
    if launch:
        # launch glow from the wall screen, room lit orange, camera shake
        a = np.asarray(c, np.float32)
        a = a + (np.array([255, 170, 70], np.float32) - a) * (0.55 * flash)
        c = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        d = ImageDraw.Draw(c)
        plume_h = 520 * ease_out_cubic((u - 2.6) / 1.0)
        d.polygon([(500, 900), (580, 900), (620, 900 - plume_h * 0.2), (540, 900 - plume_h), (460, 900 - plume_h * 0.2)], fill=(255, 240, 200))
        dx = int(math.sin(u * 70) * 14 * flash)
        c = c.transform((W, H), Image.AFFINE, (1, 0, dx, 0, 1, dx // 2), Image.BILINEAR)
    caption(c, "POV: now I launch satellites", 1480 if not launch else 1480, u - 0.5, 60)
    return c


# --------------------------------------------------------------------------- end card (cinematic, story-style)
LOGO_IMG = Image.open(LOGO).convert("RGBA")
LOGO_IMG = LOGO_IMG.resize((int(LOGO_IMG.width * 300 / LOGO_IMG.height), 300), Image.LANCZOS)


def end_card(u):
    c = Image.new("RGB", (W, H), (0, 0, 0))
    a, dy = clamp(u / 0.5), 30 * (1 - ease_out_cubic(u / 0.6))
    place(c, text_img("your job could be", F_UI_R, 72, (230, 230, 235)), W / 2, 700 + dy, 1, a)
    if u >= 0.35:
        k = u - 0.35
        place(c, text_img("weird too.", F_SERIF_I, 170, (255, 205, 110)), W / 2, 850, ease_out_back(k / 0.3, 1.4))
    if u >= 0.9:
        place(c, LOGO_IMG, W / 2, 1180, 1, clamp((u - 0.9) / 0.4))
    if u >= 1.2:
        place(c, text_img("camouroles.pages.dev", F_UI, 56, (255, 255, 255)), W / 2, 1400, 1, clamp((u - 1.2) / 0.3))
    if u >= 1.5:
        place(c, text_img("follow for more glow-ups", F_UI_R, 44, (150, 150, 160)), W / 2, 1490, 1, clamp((u - 1.5) / 0.3))
    return c


# --------------------------------------------------------------------------- frame assembly
rng = np.random.default_rng(4)
GRAIN = [rng.normal(0, 6, (H, W, 1)).astype(np.float32) for _ in range(4)]
yy, xx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.22 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2).clip(0, 1))[..., None].astype(np.float32)


def render(t):
    if t < T_BUZZ:
        u = t
        img = grey_grade(office_frame(t), 0.7)
        img = zoom(img, 1.0 + 0.08 * ease_in_out(u / 3.2), W / 2, 800)
        caption(img, "POV: monday, 9:00", 260, u - 0.1)
        caption(img, "excel. again.", 1620, u - 0.8)
        caption(img, "is this it?", 1740, u - 1.9)
    elif t < T_PHONE:
        img = scene_buzz(t - T_BUZZ)
        if t > T_PHONE - 0.3:  # zoom into the phone screen
            k = ease_in((t - (T_PHONE - 0.3)) / 0.3)
            img = Image.blend(zoom(img, 1 + 3 * k, W / 2, 1240), scene_phone(0), k)
    elif t < T_LATER:
        img = scene_phone(t - T_PHONE)
    elif t < T_MISSION:
        img = scene_later(t - T_LATER)
    elif t < T_END:
        img = mission(t - T_MISSION)
    else:
        img = end_card(t - T_END)
        if t - T_END < 0.15:
            img = Image.blend(img, Image.new("RGB", (W, H), (255, 245, 220)), 1 - (t - T_END) / 0.15)
    a = np.asarray(img, np.float32) * VIG + GRAIN[int(t * FPS) % 4]
    return np.clip(a, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- soundtrack
SR = 44100
N = int(SR * DUR)
add, env_exp, noise, hp, note = base.add, base.env_exp, base.noise, base.hp, base.note


def tick():
    n = int(0.03 * SR)
    return hp(noise(n, 1)) * env_exp(n, 0.004) * 0.5


def lofi_keys(freqs, start, length, L):
    for f in freqs:
        add(L, start, note(f, length, (1, 0.3, 0.1), length * 0.4) * np.linspace(1, 0.6, int(length * SR)), 0.09)


def vibrate(length):
    n = int(length * SR)
    tt = np.arange(n) / SR
    return np.sign(np.sin(2 * np.pi * 150 * tt)) * (np.sin(2 * np.pi * 12 * tt) > 0) * 0.25


def drum(seed, f=60):
    n = int(0.6 * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * np.cumsum(f + 60 * np.exp(-tt * 25)) / SR) * env_exp(n, 0.25) + 0.3 * hp(noise(n, seed)) * env_exp(n, 0.04))


def brass(freqs, length):
    n = int(length * SR)
    tt = np.arange(n) / SR
    x = sum(np.tanh(2 * np.sin(2 * np.pi * f * tt)) for f in freqs) / len(freqs)
    return x * np.minimum(1, tt / 0.25) * np.minimum(1, (length - tt) / 0.5).clip(0, 1)


def rumble(length):
    n = int(length * SR)
    x = noise(n, 9)
    x = np.convolve(x, np.ones(80) / 80, "same")  # low-passed noise
    return x * np.minimum(1, np.arange(n) / (0.1 * SR)) * np.exp(-np.arange(n) / (SR * 1.6)) * 6


# (line, start time, speed-up) — lines are trimmed WAVs in vo/
VO = [("01", 0.3, 1.0), ("02", 3.5, 1.0), ("03", 5.5, 1.3), ("04", 8.45, 1.0), ("05", 10.0, 1.0), ("06", 13.2, 1.0)]


def load_vo(path, tempo):
    if tempo != 1.0:
        fast = path.replace(".wav", f"_x{tempo}.wav")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-af", f"atempo={tempo}", fast], check=True)
        path = fast
    with wave.open(path) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
        if w.getnchannels() == 2:
            x = x.reshape(-1, 2).mean(1)
    return x / (np.abs(x).max() + 1e-9) * 0.8


def build_audio():
    L = np.zeros(N)
    # office: dull lo-fi chords + clock ticks
    for i, ch in enumerate(((220.0, 261.6, 329.6), (196.0, 246.9, 293.7))):
        lofi_keys(ch, i * 1.6, 1.7, L)
    for s in range(1, 6):
        add(L, s * 0.6 + 0.1, tick(), 0.6)
    # phone buzz + notification chime
    add(L, T_BUZZ + 0.25, vibrate(0.75), 0.5)
    add(L, T_BUZZ + 0.35, note(1318.5, 0.4, (1, 0.3), 0.15), 0.3)
    add(L, T_BUZZ + 0.47, note(1760.0, 0.5, (1, 0.3), 0.2), 0.3)
    # phone scene: light pluck beat starts (hope)
    for i in range(int(2.8 / 0.375)):
        add(L, T_PHONE + i * 0.375, note((523.3, 659.3, 784.0, 659.3)[i % 4], 0.3, (1, 0.25), 0.08), 0.18)
        if i % 2 == 0:
            add(L, T_PHONE + i * 0.375, drum(i, 70) * 0.5, 0.4)
    add(L, T_PHONE + 1.85, note(1046.5, 0.3, (1, 0.3), 0.1), 0.35)  # "Applied" ding
    # "6 months later": rising swell + calendar flicks
    n = int(1.0 * SR)
    sw = noise(n, 3) * np.linspace(0, 1, n) ** 2 * 0.4
    add(L, T_LATER, sw, 1.0)
    for i in range(7):
        add(L, T_LATER + i * 0.09, tick(), 0.8)
    # mission control: cinematic drums + brass + countdown beeps
    for i in range(int(2.6 / 0.25)):
        add(L, T_MISSION + i * 0.25, note(880, 0.08, (1,), 0.02), 0.25)  # countdown beeps
        add(L, T_MISSION + i * 0.25, drum(i, 55), 0.35 + 0.04 * i)
    add(L, T_MISSION, brass((73.4, 110.0, 146.8), 2.6), 0.35)
    add(L, T_MISSION + 2.6, rumble(2.4), 0.8)  # liftoff
    add(L, T_MISSION + 2.6, brass((73.4, 110.0, 146.8, 185.0, 220.0), 1.8), 0.5)
    # end: soft chord
    for f in (293.7, 370.0, 440.0, 587.3):
        add(L, T_END + 0.35, note(f, 2.2, (1, 0.4, 0.2), 0.9), 0.12)
    # voiceover (Windows "Zira"), music ducks under each line
    V = np.zeros(N)
    for name, start, tempo in VO:
        x = load_vo(os.path.join(HERE, "vo", f"t_{name}.wav"), tempo)
        add(V, start, x, 1.0)
    room = V.copy()
    for d_, g in ((0.023, 0.18), (0.041, 0.12), (0.067, 0.08)):  # a little room so it sounds less dry
        k = int(d_ * SR)
        room[k:] += V[:-k] * g
    duck = np.convolve((np.abs(V) > 0.01).astype(float), np.ones(int(0.25 * SR)) / int(0.25 * SR), "same")
    L = L * (1 - 0.6 * np.clip(duck * 3, 0, 1))
    L = np.tanh(L * 1.4) / np.tanh(1.4) * 0.8 + room * 0.95
    R = np.roll(L, int(0.012 * SR)) * 0.95 + room * 0.05
    st = np.stack([L, R], 1)
    st /= max(1.0, np.abs(st).max() / 0.98)
    fade = np.ones(N)
    fade[-int(0.6 * SR):] = np.linspace(1, 0, int(0.6 * SR))
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
