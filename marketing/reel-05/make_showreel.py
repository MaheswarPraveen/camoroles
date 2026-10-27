"""CamouRoles brand showreel — 30 s, 9:16 (1080x1920), all graphics + music generated here.

Sections (seconds):
  0.0  dot -> compass star -> wordmark morphs in (variable font weight/width)
  3.5  logo constructed from geometry (circles, arcs, guides) -> real logo + gold sweep
  7.5  kinetic type: hidden / niche / verified / weird, marquees
 11.5  dot-grid world map: job pins pop, arcs connect, 10,000+ counter
 15.5  product motion: layered job cards stream, one expands, match ring fills
 20.0  AI recruiter: chat, filter chips snap in, radar sweep
 24.0  particle swarm -> logo silhouette
 27.5  lockup + tagline + url
Run:  python make_showreel.py  ->  camouroles_showreel_30s.mp4
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
import make_reel as base  # noqa: E402  (easing, text cache, audio helpers)

from make_reel import clamp, ease_out_back, ease_out_cubic, ease_in_out  # noqa: E402

W, H, FPS, DUR = 1080, 1920, 30, 30.0
OUT = os.path.join(HERE, "camouroles_showreel_30s.mp4")
WAV = os.path.join(HERE, "showreel.wav")
LOGO_PATH = os.path.join(HERE, "..", "..", "static", "logo-maroon.png")

CREAM = (244, 238, 226)
PAPER = (250, 246, 238)
MAROON = (112, 26, 43)
DEEP = (52, 10, 22)
GOLD = (197, 160, 89)
GOLD_L = (232, 200, 130)
INK = (26, 18, 20)
MUTED = (140, 120, 118)
CORAL = (232, 96, 76)

FONTS = "C:/Windows/Fonts/"
F_VAR = FONTS + "bahnschrift.ttf"
F_SERIF = FONTS + "BOD_B.TTF"
F_SERIF_I = FONTS + "BOD_I.TTF"
F_UI = FONTS + "segoeuib.ttf"
F_UI_R = FONTS + "segoeui.ttf"
F_MONO = FONTS + "consolab.ttf"

S = {"intro": 0.0, "build": 3.5, "type": 7.5, "map": 11.5, "cards": 15.5, "ai": 20.0, "swarm": 24.0, "end": 27.5}
ORDER = list(S)


def ease_in(x):
    x = clamp(x)
    return x * x * x


def lerp(a, b, k):
    return a + (b - a) * k


def mix(c1, c2, k):
    return tuple(int(lerp(a, b, k)) for a, b in zip(c1, c2))


# --------------------------------------------------------------------------- type helpers
_vcache = {}


def vtext(txt, size, weight=400, width=100, fill=INK):
    """Bahnschrift with explicit weight (300-700) and width (75-100) axes."""
    key = (txt, size, int(weight), int(width), fill)
    if key in _vcache:
        return _vcache[key]
    f = ImageFont.truetype(F_VAR, size)
    f.set_variation_by_axes([int(weight), int(width)])
    x0, y0, x1, y1 = f.getbbox(txt)
    im = Image.new("RGBA", (x1 - x0 + 20, y1 - y0 + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - x0, 10 - y0), txt, font=f, fill=fill)
    if len(_vcache) > 3000:
        _vcache.clear()
    _vcache[key] = im
    return im


def text(txt, font, size, fill=INK):
    return base.text_img(txt, font, size, fill)


def place(c, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    base.place(c, im, cx, cy, scale, rot, alpha)


def fade_in(u, start, dur=0.35):
    return ease_out_cubic((u - start) / dur)


# --------------------------------------------------------------------------- shared art
LOGO = Image.open(LOGO_PATH).convert("RGBA")


def logo_at(h):
    return LOGO.resize((int(LOGO.width * h / LOGO.height), h), Image.LANCZOS)


LOGO_BIG = logo_at(820)
LOGO_MID = logo_at(560)


def star(d, cx, cy, r, fill, thin=0.18):
    """Four-point compass star like the one inside the logo."""
    pts = []
    for i in range(8):
        a = -math.pi / 2 + i * math.pi / 4
        rr = r if i % 2 == 0 else r * thin
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts, fill=fill)


def paper_bg(c, t, tone=CREAM):
    c.paste(tone, (0, 0, W, H))
    d = ImageDraw.Draw(c)
    # faint drifting guide grid: the "design system" feel
    off = (t * 18) % 90
    for x in range(-90, W + 90, 90):
        d.line((x + off, 0, x + off, H), fill=mix(tone, MUTED, 0.08), width=1)
    for y in range(-90, H + 90, 90):
        d.line((0, y + off, W, y + off), fill=mix(tone, MUTED, 0.08), width=1)


def corner_marks(c, t):
    """Registration marks + running timecode: reads as a showreel."""
    d = ImageDraw.Draw(c)
    for (x, y, sx, sy) in ((60, 60, 1, 1), (W - 60, 60, -1, 1), (60, H - 60, 1, -1), (W - 60, H - 60, -1, -1)):
        d.line((x, y, x + 50 * sx, y), fill=MAROON, width=3)
        d.line((x, y, x, y + 50 * sy), fill=MAROON, width=3)
    tc = f"CR—SHOWREEL  {int(t):02d}:{int((t % 1) * FPS):02d}"
    im = text(tc, F_MONO, 30, MAROON)
    c.paste(im, (90, H - 120), im)
    sec = [n for n in ORDER if t >= S[n]][-1]
    lab = text(f"{ORDER.index(sec) + 1:02d} / {sec.upper()}", F_MONO, 30, MAROON)
    c.paste(lab, (W - 90 - lab.width, H - 120), lab)


# --------------------------------------------------------------------------- 1. intro: dot -> star -> wordmark
def s_intro(c, u):
    paper_bg(c, u)
    d = ImageDraw.Draw(c)
    cx, cy = W / 2, 820
    if u < 0.6:
        r = 8 + 10 * ease_out_back(u / 0.3)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD)
    else:
        k = (u - 0.6)
        r = 30 + 150 * ease_out_back(k / 0.5, 1.4)
        # rays drawing out
        for i in range(16):
            a = i * math.pi / 8 + k * 0.3
            L = 340 * ease_out_cubic((k - i * 0.015) / 0.6)
            d.line((cx + math.cos(a) * r * 1.2, cy + math.sin(a) * r * 1.2,
                    cx + math.cos(a) * (r * 1.2 + L), cy + math.sin(a) * (r * 1.2 + L)), fill=mix(CREAM, GOLD, 0.6), width=3)
        star(d, cx, cy, r, MAROON)
        d.ellipse((cx - 22, cy - 22, cx + 22, cy + 22), fill=GOLD)
        d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=CREAM)
    if u >= 1.4:
        k = u - 1.4
        word = "CAMOUROLES"
        total = 0
        ims = []
        for i, ch in enumerate(word):
            p = clamp((k - i * 0.06) / 0.5)
            wgt = lerp(300, 700, ease_out_cubic(p))
            wid = lerp(75, 100, ease_out_cubic(p))
            im = vtext(ch, 132, wgt, wid, MAROON)
            ims.append((im, p))
            total += im.width - 14
        x = W / 2 - total / 2
        for im, p in ims:
            if p > 0:
                place(c, im, x + im.width / 2, 1240 + 60 * (1 - ease_out_back(p, 1.6)), 1, 0, clamp(p * 2))
            x += im.width - 14
    if u >= 2.4:
        place(c, text("niche jobs. real openings.", F_SERIF_I, 64, INK), W / 2, 1380, 1, 0, fade_in(u, 2.4))


# --------------------------------------------------------------------------- 2. logo construction
def s_build(c, u):
    paper_bg(c, u, PAPER)
    d = ImageDraw.Draw(c)
    cx, cy = W / 2, 900
    guide = mix(PAPER, MAROON, 0.35)
    # construction circles (golden ratio radii) draw as arcs
    for i, r in enumerate((380, 235, 145, 90)):
        k = ease_in_out((u - i * 0.18) / 0.9)
        if k > 0:
            d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * k, fill=guide, width=3)
    # axes + diagonals
    for i, (x0, y0, x1, y1) in enumerate(((cx, 380, cx, 1420), (160, cy, W - 160, cy), (220, 340, W - 220, 1460), (W - 220, 340, 220, 1460))):
        k = ease_in_out((u - 0.3 - i * 0.12) / 0.6)
        if k > 0:
            d.line((x0, y0, lerp(x0, x1, k), lerp(y0, y1, k)), fill=guide, width=2)
    # measurement labels
    for i, (lab, x, y) in enumerate((("φ 1.618", 160, 470), ("r = 380", 760, 520), ("45°", 780, 1300), ("grid 90", 140, 1330))):
        if u > 0.6 + i * 0.15:
            im = text(lab, F_MONO, 30, MAROON)
            place(c, im, x + im.width / 2, y, 1, 0, fade_in(u, 0.6 + i * 0.15, 0.2))
    # nodes
    for i, (x, y) in enumerate(((cx, cy - 380), (cx + 380, cy), (cx, cy + 380), (cx - 380, cy), (cx + 145, cy - 145))):
        k = ease_out_back((u - 0.8 - i * 0.08) / 0.25, 2.2)
        if k > 0:
            r = 12 * k
            d.ellipse((x - r, y - r, x + r, y + r), outline=MAROON, width=3, fill=PAPER)
    # the real logo is revealed by a circle growing from the construction centre
    if u >= 1.9:
        k = ease_in_out((u - 1.9) / 1.0)
        r = 560 * k
        logo = LOGO_BIG
        lx, ly = int(cx - logo.width / 2), int(cy - logo.height / 2)
        mask = Image.new("L", logo.size, 0)
        ImageDraw.Draw(mask).ellipse((logo.width / 2 - r, logo.height / 2 - r, logo.width / 2 + r, logo.height / 2 + r), fill=255)
        m = Image.fromarray(np.minimum(np.asarray(mask), np.asarray(logo.getchannel("A"))))
        if u > 2.6:  # soft glow once it has landed
            g = clamp((u - 2.6) / 0.4) * (1 - clamp((u - 3.2) / 0.3))
            glow = logo.getchannel("A").filter(ImageFilter.GaussianBlur(30)).point(lambda v: int(v * 0.45 * g))
            c.paste(GOLD_L, (lx, ly), glow)
        c.paste(logo.convert("RGB"), (lx, ly), m)
    place(c, text("brand mark · construction", F_MONO, 34, MAROON), W / 2, 1560, 1, 0, fade_in(u, 0.4))


# --------------------------------------------------------------------------- 3. kinetic type
WORDS = [("hidden", MAROON), ("niche", INK), ("verified", MAROON), ("weird", GOLD)]


def s_type(c, u):
    paper_bg(c, u, CREAM if int(u / 1.0) % 2 == 0 else PAPER)
    # marquee rows, alternating directions, weights breathing
    for row in range(9):
        y = 240 + row * 175
        direction = 1 if row % 2 else -1
        wgt = 300 + 400 * (0.5 + 0.5 * math.sin(u * 3 + row))
        im = vtext("NICHE · HIDDEN · VERIFIED · ", 120, wgt, 85, mix(CREAM, MAROON, 0.13))
        strip_w = im.width
        x = (u * 420 * direction + row * 200) % strip_w
        for k in (-1, 0, 1):
            c.paste(im, (int(x + k * strip_w - strip_w / 2), int(y - im.height / 2)), im)
    # hero word: one per beat-pair, weight + width morph in, squash out
    i = min(len(WORDS) - 1, int(u / 1.0))
    k = u - i * 1.0
    word, col = WORDS[i]
    wgt = lerp(300, 700, ease_out_cubic(k / 0.35))
    wid = lerp(75, 100, ease_out_cubic(k / 0.45))
    im = vtext(word, 300, wgt, wid, col)
    s = 1 + 0.25 * (1 - ease_out_back(k / 0.3, 1.8))
    if k > 0.82:  # squash out
        s *= 1 - ease_in((k - 0.82) / 0.18)
    box = Image.new("RGBA", (im.width + 80, im.height + 40), PAPER + (255,))
    ImageDraw.Draw(box).rectangle((0, 0, box.width - 1, box.height - 1), outline=col, width=6)
    box.paste(im, (40, 20), im)
    place(c, box, W / 2, 960, s, -3 + 6 * (i % 2))
    lab = ("jobs", "careers", "openings", "you")[i]
    place(c, text(lab, F_SERIF_I, 90, INK), W / 2 + 160, 1180, ease_out_back((k - 0.2) / 0.25), 4)


# --------------------------------------------------------------------------- 4. world map of openings
def land(lon, lat):
    """Very rough continent mask (enough for a stylised dot map)."""
    blobs = [(-100, 45, 32, 20), (-60, -15, 18, 26), (15, 50, 22, 12), (20, 5, 20, 28), (80, 25, 30, 18),
             (105, 45, 30, 16), (135, -25, 16, 10), (-40, 72, 14, 8), (100, 0, 14, 8), (45, 25, 12, 8)]
    for x, y, rx, ry in blobs:
        if ((lon - x) / rx) ** 2 + ((lat - y) / ry) ** 2 < 1:
            return True
    return False


MAP_DOTS = []
for gy in range(0, 26):
    for gx in range(0, 30):
        lon = -170 + gx * 12
        lat = 80 - gy * 6.2
        if land(lon, lat):
            MAP_DOTS.append((80 + gx * 31.5, 560 + gy * 30))
PINS = [("Bengaluru", 77, 13, 160), ("Hyderabad", 78, 17, 0), ("Pune", 74, 18, 0), ("Dubai", 55, 25, 0),
        ("San Francisco", -122, 37, 0), ("Seattle", -122, 47, 0), ("London", 0, 51, 0), ("Munich", 11, 48, 0),
        ("Singapore", 104, 1, 0), ("Tokyo", 139, 35, 0), ("Toronto", -79, 43, 0), ("Remote", -40, 10, 0)]


def map_xy(lon, lat):
    return 80 + (lon + 170) / 12 * 31.5, 560 + (80 - lat) / 6.2 * 30


def s_map(c, u):
    paper_bg(c, u, PAPER)
    d = ImageDraw.Draw(c)
    for i, (x, y) in enumerate(MAP_DOTS):
        a = clamp((u * 3 - (x / W)) * 2)
        if a > 0:
            r = 7 * a
            d.ellipse((x - r, y - r, x + r, y + r), fill=mix(PAPER, MAROON, 0.55))
    home = map_xy(77, 13)
    for i, (name, lon, lat, _) in enumerate(PINS):
        t0 = 0.35 + i * 0.18
        k = (u - t0) / 0.3
        if k <= 0:
            continue
        x, y = map_xy(lon, lat)
        if i > 0:  # arc from home to this pin
            ak = ease_in_out((u - t0) / 0.5)
            mx_, my_ = (home[0] + x) / 2, min(home[1], y) - 180
            pts = []
            for s_ in np.linspace(0, ak, 24):
                px = (1 - s_) ** 2 * home[0] + 2 * (1 - s_) * s_ * mx_ + s_ ** 2 * x
                py = (1 - s_) ** 2 * home[1] + 2 * (1 - s_) * s_ * my_ + s_ ** 2 * y
                pts.append((px, py))
            if len(pts) > 1:
                d.line(pts, fill=GOLD, width=3)
        e = ease_out_back(k, 2.4)
        r = 16 * e
        pulse = 16 + 40 * ((u * 1.5 + i * 0.3) % 1)
        d.ellipse((x - pulse, y - pulse, x + pulse, y + pulse), outline=mix(PAPER, MAROON, 0.4), width=2)
        d.ellipse((x - r, y - r, x + r, y + r), fill=MAROON, outline=PAPER, width=4)
        if name in ('Bengaluru', 'Dubai', 'San Francisco', 'London', 'Tokyo'):
            lab = text(name, F_UI, 34, INK)
            place(c, lab, x, y + (54 if name == 'Bengaluru' else -48), e)
    n = int(10000 * ease_out_cubic((u - 0.4) / 2.6))
    place(c, vtext(f"{n:,}+", 230, 700, 85, MAROON), W / 2, 330)
    place(c, text("verified openings, mapped live", F_UI_R, 48, INK), W / 2, 470, 1, 0, fade_in(u, 0.5))
    place(c, text("direct from company career pages", F_SERIF_I, 58, MAROON), W / 2, 1500, 1, 0, fade_in(u, 1.6))


# --------------------------------------------------------------------------- 5. product motion: job cards
CARD_DATA = [("Flight Software Engineer", "Bengaluru · 1–3 yrs"), ("Robotics Perception Eng.", "Remote · 2–4 yrs"),
             ("Quant Researcher", "Mumbai · 0–2 yrs"), ("Fusion Controls Engineer", "Remote · 3–6 yrs"),
             ("Embedded Firmware Eng.", "Pune · 2–4 yrs"), ("Chip Design Engineer", "Hyderabad · 1–3 yrs"),
             ("AI Research Engineer", "Bengaluru · 2–5 yrs"), ("Satellite Data Engineer", "Remote · 1–3 yrs")]


def job_card(title, meta, w=760, accent=MAROON):
    im = Image.new("RGBA", (w + 24, 210), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((16, 20, w + 16, 200), 34, fill=(0, 0, 0, 45))
    d.rounded_rectangle((0, 0, w, 184), 34, fill=PAPER, outline=mix(PAPER, MAROON, 0.25), width=3)
    d.rounded_rectangle((28, 34, 128, 134), 26, fill=accent)
    star(d, 78, 84, 32, CREAM)
    t = text(title, F_UI, 46, INK)
    im.paste(t, (156, 36), t)
    m = text(meta, F_UI_R, 36, MUTED)
    im.paste(m, (156, 100), m)
    return im


CARDS = [job_card(t, m, accent=(MAROON, DEEP, GOLD)[i % 3]) for i, (t, m) in enumerate(CARD_DATA)]


def s_cards(c, u):
    paper_bg(c, u, CREAM)
    # three parallax columns of cards scrolling at different speeds
    lanes = [(-260, 0.55, 260), (W / 2, 1.0, 420), (W + 260, 0.75, 330)]
    pick_t = 2.0
    for li, (x, scale, speed) in enumerate(lanes):
        for j in range(10):
            idx = (j + li * 3) % len(CARDS)
            y = ((j * 240 - u * speed) % 2400) - 240
            if li == 1 and u > pick_t and abs(y - 960) < 140:
                continue
            a = 0.45 if li != 1 else (1 - 0.6 * clamp((u - pick_t) / 0.4))
            place(c, CARDS[idx], x, y, scale, 0, a)
    if u >= pick_t:  # one card lifts out and expands into a detail view
        k = ease_out_back((u - pick_t) / 0.5, 1.3)
        dd = Image.new("RGBA", (920, 760), (0, 0, 0, 0))
        g = ImageDraw.Draw(dd)
        g.rounded_rectangle((18, 24, 918, 758), 46, fill=(0, 0, 0, 50))
        g.rounded_rectangle((0, 0, 900, 736), 46, fill=PAPER, outline=MAROON, width=5)
        g.rounded_rectangle((44, 44, 164, 164), 30, fill=MAROON)
        star(g, 104, 104, 40, CREAM)
        t1 = text("Flight Software Engineer", F_UI, 56, INK)
        dd.paste(t1, (196, 52), t1)
        t2 = text("Satellite startup · Bengaluru", F_UI_R, 40, MUTED)
        dd.paste(t2, (196, 124), t2)
        for j, sk in enumerate(("C++", "RTOS", "Orbital mechanics")):
            chip = text(sk, F_UI, 36, MAROON)
            x0 = 44 + sum(text(s2, F_UI, 36, MAROON).width + 60 for s2 in ("C++", "RTOS", "Orbital mechanics")[:j])
            g.rounded_rectangle((x0, 230, x0 + chip.width + 40, 290), 30, outline=MAROON, width=3)
            dd.paste(chip, (x0 + 20, 238), chip)
        # match ring
        pct = 96 * ease_out_cubic((u - pick_t - 0.4) / 1.2)
        g.ellipse((560, 340, 860, 640), outline=mix(PAPER, MAROON, 0.15), width=26)
        g.arc((560, 340, 860, 640), -90, -90 + 360 * pct / 100, fill=GOLD, width=26)
        p = text(f"{int(pct)}%", F_UI, 84, MAROON)
        dd.paste(p, (710 - p.width // 2, 430), p)
        f_ = text("fit", F_UI_R, 40, MUTED)
        dd.paste(f_, (710 - f_.width // 2, 530), f_)
        for j, line in enumerate(("Matches your CV:", "embedded C++ · 2 yrs", "space + coding")):
            tl = text(line, F_UI if j == 0 else F_UI_R, 44, INK if j == 0 else MAROON)
            dd.paste(tl, (44, 360 + j * 74), tl)
        g.rounded_rectangle((44, 600, 480, 690), 45, fill=MAROON)
        ap = text("Apply direct", F_UI, 46, CREAM)
        dd.paste(ap, (262 - ap.width // 2, 618), ap)
        place(c, dd, W / 2, 960, lerp(0.4, 1.0, k))
    place(c, text("every card is a real opening", F_SERIF_I, 58, MAROON), W / 2, 1560, 1, 0, fade_in(u, 0.3))


# --------------------------------------------------------------------------- 6. AI recruiter
def s_ai(c, u):
    paper_bg(c, u, PAPER)
    d = ImageDraw.Draw(c)
    # radar behind
    cx, cy = W / 2, 1280
    for r in (160, 300, 440):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=mix(PAPER, MAROON, 0.18), width=3)
    ang = u * 2.2
    sweep = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sweep)
    for j in range(30):
        a = ang - j * 0.02
        sd.line((cx, cy, cx + math.cos(a) * 440, cy + math.sin(a) * 440), fill=GOLD + (int(150 * (1 - j / 30)),), width=6)
    c.paste(sweep, (0, 0), sweep)
    rnd = random.Random(5)
    for j in range(14):  # blips light up as the sweep passes
        a = rnd.uniform(0, 6.28)
        r = rnd.uniform(80, 430)
        bx, by = cx + math.cos(a) * r, cy + math.sin(a) * r
        lit = math.cos(ang - a) > 0.96
        rr = 12 if lit else 7
        d.ellipse((bx - rr, by - rr, bx + rr, by + rr), fill=GOLD if lit else mix(PAPER, MAROON, 0.4))
    place(c, vtext("AI RECRUITER", 120, 700, 80, MAROON), W / 2, 230, ease_out_back(u / 0.3, 1.6))

    def bubble(txt, mine):
        t = text(txt, F_UI, 48, CREAM if mine else INK)
        im = Image.new("RGBA", (t.width + 64, t.height + 44), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 36, fill=MAROON if mine else CREAM, outline=MAROON, width=3)
        im.paste(t, (32, 22), t)
        return im
    ask = "space + coding, 2 yrs, India or remote"
    n = int(len(ask) * clamp((u - 0.3) / 0.9))
    if u >= 0.3:
        b = bubble(ask[:n] or " ", True)
        place(c, b, W - 60 - b.width / 2, 400)
    if u >= 1.4:
        b = bubble("Got it. Searching 10,000+ openings", False)
        place(c, b, 60 + b.width / 2, 540, ease_out_back((u - 1.4) / 0.25))
    chips = [("Space & Aerospace", MAROON), ("India", DEEP), ("Remote", DEEP), ("1–3 yrs", GOLD)]
    x, row = 70, 0
    for j, (lab, col) in enumerate(chips):
        t0 = 1.8 + j * 0.22
        t = text(lab, F_UI, 40, CREAM)
        w_ = t.width + 50
        if x + w_ > W - 70:  # wrap to a second row
            x, row = 70, row + 1
        if u >= t0:
            k = ease_out_back((u - t0) / 0.25, 2.2)
            chip = Image.new("RGBA", (w_, 74), (0, 0, 0, 0))
            ImageDraw.Draw(chip).rounded_rectangle((0, 0, w_ - 1, 73), 37, fill=col)
            chip.paste(t, (25, 12), t)
            yy = 690 + row * 96 - 160 * (1 - k)
            place(c, chip, x + w_ / 2, yy, k)
        x += w_ + 16
    if u >= 3.0:
        place(c, text("23 roles fit you", F_SERIF_I, 80, MAROON), W / 2, 900, ease_out_back((u - 3.0) / 0.3))


# --------------------------------------------------------------------------- 7. particle swarm -> logo
def logo_targets(n=2600, h=900):
    lg = logo_at(h)
    a = np.asarray(lg.getchannel("A"))
    ys, xs = np.nonzero(a[::6, ::6] > 160)
    idx = np.random.default_rng(2).choice(len(xs), size=min(n, len(xs)), replace=False)
    tx = xs[idx] * 6 + (W - lg.width) / 2
    ty = ys[idx] * 6 + 940 - lg.height / 2
    return tx.astype(np.float32), ty.astype(np.float32)


TX, TY = logo_targets()
NP = len(TX)
_r = np.random.default_rng(9)
SX = _r.uniform(-200, W + 200, NP).astype(np.float32)
SY = _r.uniform(-200, H + 200, NP).astype(np.float32)
PHASE = _r.uniform(0, 6.28, NP).astype(np.float32)
PCOL = np.where(_r.random(NP) < 0.25, 1, 0)


def s_swarm(c, u):
    paper_bg(c, u, CREAM)
    k = ease_in_out((u - 0.4) / 2.2)
    swirl = (1 - k) * 160
    x = lerp(SX, TX, k) + np.cos(PHASE + u * 3) * swirl
    y = lerp(SY, TY, k) + np.sin(PHASE + u * 3) * swirl
    a = np.asarray(c).copy()
    r = 3 if k < 0.9 else 3
    for col_id, col in ((0, MAROON), (1, GOLD)):
        m = PCOL == col_id
        xi = np.clip(x[m].astype(int), r, W - r - 1)
        yi = np.clip(y[m].astype(int), r, H - r - 1)
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    a[yi + dy, xi + dx] = col
    img = Image.fromarray(a)
    c.paste(img)
    if u > 2.4:  # the real logo resolves out of the swarm
        place(c, logo_at(900), W / 2, 940, 1, 0, ease_in_out((u - 2.4) / 0.9))
    place(c, text("10,000 openings. one place.", F_SERIF_I, 62, MAROON), W / 2, 1560, 1, 0, fade_in(u, 0.6))


# --------------------------------------------------------------------------- 8. end lockup
def s_end(c, u):
    paper_bg(c, u + S["end"], CREAM)
    d = ImageDraw.Draw(c)
    # the logo from the swarm glides up and shrinks into the lockup position
    k = ease_in_out(u / 0.9)
    h = int(lerp(900, 560, k))
    place(c, logo_at(h), W / 2, lerp(940, 700, k))
    if u >= 0.6:
        kk = u - 0.6
        p = ease_out_cubic(kk / 0.6)
        im = vtext("CAMOUROLES", 150, lerp(300, 700, p), lerp(75, 100, p), MAROON)
        place(c, im, W / 2, 1150, 1, 0, clamp(kk * 3))
    if u >= 0.9:  # thin gold rule draws out from the centre
        half = 300 * ease_in_out((u - 0.9) / 0.5)
        d.line((W / 2 - half, 1255, W / 2 + half, 1255), fill=GOLD, width=4)
    if u >= 1.1:
        place(c, text("niche jobs. real openings.", F_SERIF_I, 70, INK), W / 2, 1345, 1, 0, fade_in(u, 1.1))
    if u >= 1.45:
        place(c, text("camouroles.pages.dev", F_UI, 46, MAROON), W / 2, 1450, 1, 0, fade_in(u, 1.45))


SCENES = {"intro": s_intro, "build": s_build, "type": s_type, "map": s_map,
          "cards": s_cards, "ai": s_ai, "swarm": s_swarm, "end": s_end}


# --------------------------------------------------------------------------- transitions + assembly
def scene_frame(name, t):
    c = Image.new("RGB", (W, H), CREAM)
    SCENES[name](c, t - S[name])
    return c


def render(t):
    name = [n for n in ORDER if t >= S[n]][-1]
    i = ORDER.index(name)
    img = scene_frame(name, t)
    # transition into the next scene: a maroon shutter (alternating directions) or a circle iris
    if i + 1 < len(ORDER) and ORDER[i + 1] != "end":
        nxt = ORDER[i + 1]
        dt = S[nxt] - t
        if dt < 0.35:
            k = ease_in(1 - dt / 0.35)
            mask = Image.new("L", (W, H), 0)
            md = ImageDraw.Draw(mask)
            style = i % 3
            if style == 0:  # diagonal blinds
                for j in range(12):
                    x = j * 120 - 400
                    md.polygon([(x, 0), (x + 120 * k + 1, 0), (x + 120 * k + 400, H), (x + 400, H)], fill=255)
            elif style == 1:  # circle iris from centre
                r = 1300 * k
                md.ellipse((W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r), fill=255)
            else:  # horizontal shutters
                for j in range(16):
                    y = j * 120
                    md.rectangle((0, y, W, y + 120 * k), fill=255)
            img.paste(scene_frame(nxt, S[nxt]), (0, 0), mask)
    corner_marks(img, t)
    a = np.asarray(img, np.float32) + GRAIN[int(t * FPS) % 3]
    return np.clip(a, 0, 255).astype(np.uint8)


GRAIN = [np.random.default_rng(k).normal(0, 3.5, (H, W, 1)).astype(np.float32) for k in range(3)]


# --------------------------------------------------------------------------- soundtrack: 120 BPM electronic
SR = 44100
N = int(SR * DUR)
add, env_exp, noise, hp, note = base.add, base.env_exp, base.noise, base.hp, base.note
B = 0.5


def build_audio():
    L = np.zeros(N)
    chords = [(220.0, 277.2, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7), (164.8, 207.7, 246.9)]  # A F G E
    roots = [55.0, 43.65, 49.0, 41.2]
    nb = int(DUR / B)
    for bt in range(nb):
        t = bt * B
        bar = (bt // 4) % 4
        intro = t < S["build"]
        outro = t >= S["end"] + 1.5
        if not intro and not outro:
            add(L, t, base.kick(), 0.8)
            if bt % 2 == 1:
                add(L, t, base.clap(bt), 0.45)
            for h in range(2):
                add(L, t + h * B / 2, base.hat(bt * 2 + h, 0.04), 0.4 if h else 0.2)
            add(L, t + B / 2, note(roots[bar] * 2, B / 2, (1, 0.5, 0.2), 0.12), 0.45)
        # pad + arp always (sparser in intro)
        if bt % 4 == 0:
            add(L, t, sum(note(f, 2.0, (1, 0.3), 0.9) for f in chords[bar]) / 3, 0.18)
        for h in range(4 if not intro else 2):
            f = chords[bar][(bt * 4 + h) % 3] * 2
            add(L, t + h * B / (4 if not intro else 2), note(f, 0.16, (1, 0.25), 0.05), 0.11)
    for n in ORDER[1:]:
        add(L, S[n] - 0.6, base.riser(0.6), 0.45)
        add(L, S[n], base.boom(), 0.45)
    add(L, S["map"] + 0.4, base.blip(1400), 0.2)
    for j in range(12):
        add(L, S["map"] + 0.35 + j * 0.18, base.blip(880 * 2 ** ((j % 5) / 12)), 0.18)
    add(L, S["cards"] + 2.0 + 1.6, note(1318.5, 0.6, (1, 0.4), 0.25), 0.3)
    for j in range(len("space + coding, 2 yrs, India or remote")):
        add(L, S["ai"] + 0.3 + j * 0.024, base.hat(900 + j, 0.015), 0.5)
    for f in (440.0, 554.4, 659.3, 880.0):
        add(L, S["end"] + 0.1, note(f, 2.4, (1, 0.4, 0.2), 1.0), 0.12)
    R = np.roll(L, int(0.012 * SR)) * 0.95
    st = np.stack([L, R], 1)
    st = np.tanh(st * 1.3) / np.tanh(1.3)
    fade = np.ones(N)
    fade[-int(0.8 * SR):] = np.linspace(1, 0, int(0.8 * SR))
    st *= fade[:, None] * 0.88
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
        if i % 150 == 0:
            print(f"frame {i}", flush=True)
    proc.stdin.close()
    proc.wait()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-c:v", "libx264", "-preset", "slow", "-crf", "21",
                    "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", OUT], check=True)
    os.remove(raw)
    print("done:", OUT)


if __name__ == "__main__":
    main()
