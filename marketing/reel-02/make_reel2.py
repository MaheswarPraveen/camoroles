"""CamouRoles reel #2 — 15 s, 9:16. Glitch-feed open + scene-to-scene transitions, phonk-style track.

Reuses the drawing helpers and scenes from reel-01 (make_reel.py) and adds the transitions:
feed glitch/tear -> zoom through the "O" -> text-mask wipe -> torn strips + diagonal slice ->
"+" morph -> card flip -> spin collapse -> logo burst.
Run:  python make_reel2.py   ->  camouroles_reel_02_transitions.mp4
"""
import math
import os
import random
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "reel-01"))
import make_reel as base  # noqa: E402  (helpers, colours, fonts, scenes)

from make_reel import (W, H, FPS, BLACK, WHITE, PINK, LIME, CYAN, VIOLET, ORANGE, YELLOW, BLUE, RED,  # noqa: E402
                       F_IMPACT, F_BLACK, F_BOLD, F_ERAS, F_ROCK, F_BERLIN,
                       clamp, ease_out_back, ease_out_cubic, ease_in_out, text_img, place, glitch_text, sticker, marquee, fit_size)

OUT = os.path.join(HERE, "camouroles_reel_02_sunset.mp4")
WAV = os.path.join(HERE, "soundtrack2.wav")
DUR = 15.0
BPM = 140
B = 60 / BPM

# Segment lengths in seconds (sum = 15)
SEGS = [("feed", 2.0), ("stop", 1.4), ("hiding", 1.6), ("strips", 2.6), ("count", 1.6),
        ("agent", 2.2), ("comments", 1.6), ("end", 2.0)]
STARTS = {}
_t = 0.0
for name, length in SEGS:
    STARTS[name] = (_t, length)
    _t += length


def ease_in(x):
    x = clamp(x)
    return x * x * x


def blank(color=BLACK):
    return Image.new("RGB", (W, H), color)


def base_scene(fn, u):
    c = blank()
    fn(c, u)
    return c


# --------------------------------------------------------------------------- reel #2 look: "sunset chrome"
INDIGO = (24, 18, 62)
CORAL = (255, 94, 98)
PEACH = (255, 182, 140)
SKY = (96, 200, 255)
MINT = (84, 240, 190)
LILAC = (178, 142, 255)
CHROME = (228, 232, 242)


def bg(c, color):
    c.paste(color, (0, 0, W, H))


def scene_plot(c, u):
    bg(c, CORAL)
    marquee(c, "PLOT TWIST  PLOT TWIST", INDIGO, 300, u * 500, 130, 0.13)
    marquee(c, "PLOT TWIST  PLOT TWIST", INDIGO, 1660, -u * 500, 130, 0.13)
    dx, dy = base.shake(u, 0.12)
    s = 1 + 2.4 * (1 - ease_out_cubic(u / 0.16))
    glitch_text(c, "PLOT", F_IMPACT, 430, CHROME, W / 2 + dx, PLOT_Y + dy, s, 0, split=12, stroke=10, stroke_fill=INDIGO)
    if u >= 0.32:
        k = u - 0.32
        glitch_text(c, "TWIST", F_IMPACT, 300, INDIGO, W / 2, 1150, ease_out_back(k / 0.2), -4, split=8)


def scene_dream(c, u):
    bg(c, INDIGO)
    marquee(c, "PSST  PSST  PSST", LILAC, 260, u * 400, 130, 0.12)
    place(c, text_img("your dream job", F_BLACK, 118, CHROME), W / 2, 620, ease_out_back(u / 0.2), -2)
    if u >= 0.22:
        k = u - 0.22
        dx, dy = base.shake(k, 0, 0.14, 18, 3)
        glitch_text(c, "EXISTS", F_IMPACT, 290, MINT, W / 2 + dx, 830 + dy, ease_out_back(k / 0.18), 3, split=10)
    if u >= 0.6:
        k = u - 0.6
        place(c, text_img("it's just not", F_BLACK, 92, PEACH), W / 2, 1110, ease_out_back(k / 0.2))
        place(c, text_img("on your feed", F_BLACK, 92, PEACH), W / 2, 1220, ease_out_back((k - 0.05) / 0.2))


def scene_count2(c, u):
    bg(c, SKY)
    marquee(c, "DIDN'T KNOW  DIDN'T KNOW", INDIGO, 330, u * 450, 130, 0.1)
    n = int(10000 * ease_out_cubic(u / 0.55))
    dx, dy = base.shake(u, 0.55, 0.15, 20, 5)
    glitch_text(c, f"{n:,}+", F_IMPACT, 300, INDIGO, W / 2 + dx, 760 + dy, 1, -2, split=10, stroke=8, stroke_fill=CHROME)
    if u >= 0.6:
        k = u - 0.6
        place(c, text_img("roles you didn't", F_BLACK, 104, INDIGO), W / 2, 1010, ease_out_back(k / 0.2), 2)
        place(c, text_img("know existed", F_BLACK, 104, CHROME, 5, INDIGO), W / 2, 1130, ease_out_back((k - 0.06) / 0.2), -2)


def bubble2(txt, fill, ink, chars=None):
    shown = txt if chars is None else txt[:chars]
    t = text_img(shown or " ", F_BLACK, 60, ink)
    w, h = max(t.width + 56, 120), t.height + 40
    im = Image.new("RGBA", (w + 14, h + 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 12, w + 10, h + 12), 34, fill=(10, 8, 30))
    d.rounded_rectangle((2, 2, w + 2, h + 2), 34, fill=fill, outline=(10, 8, 30), width=5)
    im.paste(t, (30, 22), t)
    return im


def chip2(title, meta, color):
    im = Image.new("RGBA", (900, 176), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 12, 896, 172), 30, fill=(10, 8, 30))
    d.rounded_rectangle((2, 2, 886, 162), 30, fill=CHROME, outline=(10, 8, 30), width=5)
    d.rounded_rectangle((26, 32, 122, 128), 22, fill=color, outline=(10, 8, 30), width=4)
    t = text_img(title, F_BLACK, 54, INDIGO)
    im.paste(t, (146, 24), t)
    m = text_img(meta, F_BOLD, 42, (90, 86, 120))
    im.paste(m, (146, 94), m)
    return im


ASK2 = "I like space + coding, 1 yr"
REPLY2 = "Got you. 23 roles mix both"
CHIPS2 = [chip2("Flight Software Eng.", "Remote  ·  0–2 yrs", CORAL), chip2("Satellite Data Engineer", "Bengaluru  ·  1–3 yrs", MINT)]


def scene_agent2(c, u):
    bg(c, INDIGO)
    marquee(c, "ASK IT ANYTHING", LILAC, 300, u * 500, 130, 0.12)
    place(c, sticker("ask it anything", MINT, INDIGO, 76, F_BLACK), W / 2, 520, ease_out_back(u / 0.2), -3)
    typed = int(len(ASK2) * clamp((u - 0.15) / 0.55))
    if u >= 0.1:
        b = bubble2(ASK2, PEACH, INDIGO, typed)
        place(c, b, W - 60 - b.width / 2, 800)
    if 0.8 <= u < 1.1:
        d = ImageDraw.Draw(c)
        for j in range(3):
            r = 16 + 8 * max(0, math.sin((u * 14) - j))
            cx = 150 + j * 70
            d.ellipse((cx - r, 1010 - r, cx + r, 1010 + r), fill=CHROME)
    if u >= 1.1:
        k = u - 1.1
        b = bubble2(REPLY2, CHROME, INDIGO)
        place(c, b, 60 + b.width / 2, 1010, ease_out_back(k / 0.18))
        for j, chip in enumerate(CHIPS2):
            kk = k - 0.2 - j * 0.16
            if kk > 0:
                place(c, chip, 60 + chip.width / 2, 1220 + j * 200 + 500 * (1 - ease_out_back(kk / 0.25, 1.3)), 1, (-1.5, 1.5)[j])
    if u >= 1.6:
        place(c, sticker("it gets you", CORAL, CHROME, 60), W / 2 + 160, 1660, ease_out_back((u - 1.6) / 0.2), 6)


def comment2(user, txt, color):
    im = Image.new("RGBA", (820, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 12, 816, 146), 30, fill=(10, 8, 30))
    d.rounded_rectangle((2, 2, 806, 136), 30, fill=CHROME, outline=(10, 8, 30), width=5)
    d.ellipse((24, 28, 104, 108), fill=color, outline=(10, 8, 30), width=4)
    u_ = text_img(user, F_BOLD, 34, (110, 104, 140))
    im.paste(u_, (126, 18), u_)
    t = text_img(txt, F_BLACK, 50, INDIGO)
    im.paste(t, (126, 62), t)
    heart = text_img("♥", F_BLACK, 48, CORAL)
    im.paste(heart, (740, 40), heart)
    return im


COMMENTS2 = [comment2(*x) for x in (("ishaan.dev", "build robots obv", SKY), ("tara.codes", "launch satellites!!", CORAL),
                                     ("rehan.ai", "train AI fr", MINT), ("nisha.chips", "chips > everything", LILAC))]


def scene_comments2(c, u):
    bg(c, PEACH)
    marquee(c, "YOUR VIBE  YOUR VIBE", INDIGO, 250, u * 600, 130, 0.1)
    place(c, text_img("which one's", F_BLACK, 110, INDIGO), W / 2, 430, ease_out_back(u / 0.18), -2)
    dx, dy = base.shake(u, 0.12, 0.15, 18, 13)
    glitch_text(c, "YOUR VIBE?", F_IMPACT, 210, CORAL, W / 2 + dx, 600 + dy, ease_out_back((u - 0.06) / 0.2), 3, split=9, stroke=8, stroke_fill=INDIGO)
    place(c, text_img("drop it below", F_BLACK, 96, INDIGO), W / 2, 785, ease_out_back((u - 0.12) / 0.2), -1)
    for j, im in enumerate(COMMENTS2):
        k = u - 0.35 - j * 0.22
        if k > 0:
            side = -1 if j % 2 else 1
            place(c, im, W / 2 + side * 30, 990 + j * 165, ease_out_back(k / 0.2, 2.2), side * 2)
    if u >= 1.2:
        y = 1700 + 18 * math.sin(u * 16)
        ImageDraw.Draw(c).polygon([(W / 2 - 60, y - 40), (W / 2 + 60, y - 40), (W / 2, y + 40)], fill=INDIGO)


def logo_tile2():
    size = 640
    im = Image.new("RGBA", (size + 40, size + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((24, 30, size + 24, size + 30), 90, fill=(10, 8, 30))
    d.rounded_rectangle((4, 4, size + 4, size + 4), 90, fill=(255, 244, 228), outline=CORAL, width=16)
    logo = base.LOGO_IMG.resize((int(base.LOGO_IMG.width * 470 / base.LOGO_IMG.height), 470), Image.LANCZOS)
    im.paste(logo, ((size + 8 - logo.width) // 2, (size + 8 - logo.height) // 2), logo)
    return im


LOGO_TILE2 = logo_tile2()
CONFETTI2 = [(random.Random(s).uniform(0, 2 * math.pi), random.Random(s + 99).uniform(500, 1300),
              (CORAL, PEACH, SKY, MINT, LILAC, CHROME)[s % 6], random.Random(s + 7).uniform(10, 26)) for s in range(70)]


def scene_end2(c, u):
    bg(c, INDIGO)
    marquee(c, "FIND YOUR WEIRD  FIND YOUR WEIRD", LILAC, 230, u * 450, 120, 0.14)
    marquee(c, "FIND YOUR WEIRD  FIND YOUR WEIRD", LILAC, 1830, -u * 450, 120, 0.14)
    d = ImageDraw.Draw(c)
    for ang, speed, col, size in CONFETTI2:
        k = clamp(u / 1.2)
        dist = speed * ease_out_cubic(k)
        x = W / 2 + math.cos(ang) * dist
        y = 640 + math.sin(ang) * dist + 500 * k * k
        if k < 1:
            d.rectangle((x - size / 2, y - size / 2, x + size / 2, y + size / 2), fill=col)
    place(c, LOGO_TILE2, W / 2, 660, ease_out_back(u / 0.35, 1.6) * 0.92, -4 + 2.5 * math.sin(u * 4))
    if u >= 0.25:
        glitch_text(c, "CAMOUROLES", F_IMPACT, 190, CHROME, W / 2, 1110, ease_out_back((u - 0.25) / 0.2), -2, split=9, stroke=9, stroke_fill=(10, 8, 30))
    if u >= 0.5:
        place(c, text_img("find your weird.", F_BLACK, 76, PEACH), W / 2, 1255, ease_out_back((u - 0.5) / 0.2))
    if u >= 0.8:
        place(c, sticker("camouroles.pages.dev", MINT, INDIGO, 60, F_BLACK), W / 2, 1395, ease_out_back((u - 0.8) / 0.22), 2)
    if u >= 1.15:
        bob = 8 * math.sin(u * 7)
        place(c, sticker("follow for daily niche drops", CORAL, CHROME, 50), W / 2, 1550 + bob, ease_out_back((u - 1.15) / 0.2), -4)
    if u >= 1.5:
        k = u - 1.5
        place(c, sticker("save this", PEACH, INDIGO, 50), W / 2 + 250, 1695, ease_out_back(k / 0.2), 8)
        place(c, sticker("link in bio", SKY, INDIGO, 50), W / 2 - 230, 1705, ease_out_back((k - 0.1) / 0.2), -7)


# --------------------------------------------------------------------------- glitch helpers
def glitch(img, amount, seed):
    """Horizontal slice displacement + RGB split. amount 0..1."""
    if amount <= 0:
        return img
    a = np.asarray(img).copy()
    rnd = random.Random(seed)
    for _ in range(int(6 + 30 * amount)):
        y = rnd.randrange(0, H - 10)
        h = rnd.randrange(8, int(30 + 160 * amount))
        dx = int(rnd.uniform(-1, 1) * 220 * amount)
        a[y:y + h] = np.roll(a[y:y + h], dx, axis=1)
    shift = int(4 + 28 * amount)
    out = a.copy()
    out[..., 0] = np.roll(a[..., 0], shift, axis=1)
    out[..., 2] = np.roll(a[..., 2], -shift, axis=1)
    return Image.fromarray(out)


def zoom_into(img, cx, cy, s):
    """View of img magnified s times around (cx, cy)."""
    w, h = W / s, H / s
    x0 = clamp(cx - w / 2, -W, W)
    y0 = clamp(cy - h / 2, -H, H)
    return img.transform((W, H), Image.EXTENT, (x0, y0, x0 + w, y0 + h), Image.BILINEAR)


# --------------------------------------------------------------------------- 1. boring feed -> glitch -> tear
BORING_JOBS = ["Sales Associate", "Data Entry Executive", "Customer Support Rep", "Back Office Executive",
               "Telecaller", "Field Sales Officer", "Office Assistant", "Sales Associate"]


def feed_card(title):
    im = Image.new("RGB", (980, 230), WHITE)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 979, 229), outline=(220, 220, 224), width=3)
    d.ellipse((36, 50, 156, 170), fill=(205, 205, 210))
    t = text_img(title, F_BOLD, 54, (60, 60, 66))
    im.paste(t, (186, 40), t)
    m = text_img("Posted 30+ days ago  ·  2,431 applicants", F_BOLD, 34, (150, 150, 158))
    im.paste(m, (186, 120), m)
    return im


FEED_CARDS = [feed_card(t) for t in BORING_JOBS]


def seg_feed(u):
    c = blank((236, 236, 240))
    d = ImageDraw.Draw(c)
    d.rectangle((0, 0, W, 210), fill=WHITE)
    place(c, text_img("Jobs for you", F_BOLD, 64, (70, 70, 76)), W / 2, 120)
    scroll = u * 260
    for j, card in enumerate(FEED_CARDS):
        y = 260 + j * 260 - scroll
        if -260 < y < H:
            c.paste(card, (50, int(y)))
    if u >= 0.75:
        k = u - 0.75
        place(c, text_img("MID.", F_IMPACT, 360, CORAL, 12, INDIGO), W / 2, 900, 1 + 2.2 * (1 - ease_out_cubic(k / 0.12)), -9)
    if u >= 1.05:
        k = u - 1.05
        place(c, sticker("you deserve better than this", INDIGO, PEACH, 52), W / 2, 1180, ease_out_back(k / 0.2), 5)
    amt = 0.15 * clamp((u - 0.7) / 0.1) + clamp((u - 1.45) / 0.55) * 1.0
    if u > 0.7:
        # little twitches before the tear
        amt += 0.35 * (1 if int(u * 20) % 3 == 0 else 0)
    c = glitch(c, clamp(amt), int(u * FPS))
    if u >= 1.75:  # tear: the screen splits and falls away onto pink
        k = ease_in((u - 1.75) / 0.25)
        bg = blank(CORAL)
        top = c.crop((0, 0, W, H // 2))
        bot = c.crop((0, H // 2, W, H))
        bg.paste(top.rotate(-6 * k, expand=False), (int(-300 * k), int(-H / 2 * k)))
        bg.paste(bot.rotate(5 * k, expand=False), (int(300 * k), int(H // 2 + H / 2 * k)))
        c = bg
    return c


# --------------------------------------------------------------------------- 2. STOP -> zoom through the "O"
_f = ImageFont.truetype(F_IMPACT, 430)
PLOT_Y = 760
_w_all = _f.getbbox("PLOT")[2]
_w_st = _f.getbbox("PL")[2]
_w_o = _f.getbbox("O")[2]
O_X = W / 2 - _w_all / 2 + _w_st + _w_o / 2
O_Y = PLOT_Y


def seg_stop(u, nxt):
    c = base_scene(scene_plot, u)
    zstart = 0.95
    if u < zstart:
        return c
    k = (u - zstart) / (SEGS[1][1] - zstart)
    s = math.exp(ease_in(k) * 4.2)  # up to ~66x
    z = zoom_into(c, O_X, O_Y, s)
    # the hole inside the O becomes a window onto the next scene
    r = 52 * s
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse((W / 2 - r * 0.62, H / 2 - r, W / 2 + r * 0.62, H / 2 + r), fill=255)
    z.paste(nxt, (0, 0), mask)
    return z


# --------------------------------------------------------------------------- 3. hiding -> "NICHE" text-mask wipe
NICHE_MASK = text_img("WEIRD", F_IMPACT, 420, (255, 255, 255))


def seg_hiding(u, nxt):
    c = base_scene(scene_dream, u)
    wstart = SEGS[2][1] - 0.45
    if u < wstart:
        return c
    k = (u - wstart) / 0.45
    s = 0.6 + 30 * ease_in(k)
    m = NICHE_MASK.getchannel("A")
    m = m.resize((max(1, int(m.width * s)), max(1, int(m.height * s))), Image.BILINEAR)
    mask = Image.new("L", (W, H), 0)
    mask.paste(m, (int(W / 2 - m.width / 2), int(H / 2 - m.height / 2)))
    c.paste(nxt, (0, 0), mask)
    # outline of the word sliding in, so the wipe reads as text
    if k < 0.5:
        place(c, text_img("WEIRD", F_IMPACT, 420, BLACK), W / 2 + (1 - k * 2) * 600, H / 2, s, 0, 0.0)
    return c


# --------------------------------------------------------------------------- 4. torn strips stack -> diagonal slice
STRIP_ROLES = ["BUILD ROBOTS", "LAUNCH SATELLITES", "TRAIN AI", "DESIGN CHIPS",
               "TRADE MARKETS", "POWER FUSION", "FLY DRONES", "HACK DEFENSE"]
STRIP_COLORS = [CORAL, MINT, SKY, PEACH, LILAC, CHROME, CORAL, MINT]
STRIP_FONTS = [F_IMPACT, F_BLACK, F_ERAS, F_ROCK, F_BERLIN, F_IMPACT, F_BLACK, F_ERAS]


def torn_strip(text, color, font, seed):
    w, h = 1160, 210
    im = Image.new("RGBA", (w, h + 30), (0, 0, 0, 0))
    rnd = random.Random(seed)
    top = [(x, rnd.randint(0, 18)) for x in range(0, w + 1, 40)]
    bot = [(x, h - rnd.randint(0, 18)) for x in range(w, -1, -40)]
    d = ImageDraw.Draw(im)
    d.polygon([(x, y + 14) for x, y in top] + [(x, y + 14) for x, y in bot], fill=BLACK)  # shadow
    d.polygon(top + bot, fill=color)
    ink = BLACK if sum(color) > 420 else WHITE
    size = fit_size(text, font, 130, 1020)
    t = text_img(text, font, size, ink)
    im.paste(t, (int(w / 2 - t.width / 2), int(h / 2 - t.height / 2)), t)
    return im


STRIPS = [torn_strip(t, c_, f, i) for i, (t, c_, f) in enumerate(zip(STRIP_ROLES, STRIP_COLORS, STRIP_FONTS))]


def seg_strips(u, nxt):
    c = blank(INDIGO)
    marquee(c, "WHAT YOU COULD DO", LILAC, 240, u * 600, 140, 0.12)
    marquee(c, "WHAT YOU COULD DO", LILAC, 1720, -u * 600, 140, 0.12)
    for j, strip in enumerate(STRIPS):
        k = u - j * 0.24
        if k < 0:
            continue
        side = -1 if j % 2 else 1
        e = ease_out_back(k / 0.22, 1.4)
        x = W / 2 + side * (1 - e) * 1400
        y = 430 + j * 150
        rot = side * (6 - 2 * (j % 3)) + (1 - e) * side * 20
        place(c, strip, x, y, 1, rot)
    sstart = SEGS[3][1] - 0.38
    if u < sstart:
        return c
    # diagonal slice: three shards slide apart and fall, revealing the next scene
    k = ease_in((u - sstart) / 0.38)
    out = nxt.copy()
    shards = [
        ([(0, 0), (W, 0), (W, 380), (0, 900)], (-260, -700)),
        ([(0, 900), (W, 380), (W, 1220), (0, 1740)], (420, 260)),
        ([(0, 1740), (W, 1220), (W, H), (0, H)], (-300, 900)),
    ]
    for poly, (dx, dy) in shards:
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).polygon(poly, fill=255)
        piece = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        piece.paste(c, (0, 0), mask)
        piece = piece.rotate(dx / 60 * k, resample=Image.BILINEAR)
        out.paste(piece, (int(dx * k), int(dy * k)), piece)
    d = ImageDraw.Draw(out)
    if k < 0.6:  # bright cut lines at the moment of the slice
        for (x0, y0, x1, y1) in ((0, 900, W, 380), (0, 1740, W, 1220)):
            d.line((x0, y0, x1, y1), fill=WHITE, width=int(14 * (1 - k)))
    return out


# --------------------------------------------------------------------------- 5. counter -> "+" morph
def seg_count(u, nxt):
    c = base_scene(scene_count2, u)
    mstart = SEGS[4][1] - 0.42
    if u < mstart:
        return c
    k = (u - mstart) / 0.42
    plus = text_img("+", F_IMPACT, 300, INDIGO, 8, CHROME)
    s = 1 + 45 * ease_in(k)
    place(c, plus, W / 2 + 330 * (1 - ease_in_out(k)), 760 + 140 * ease_in_out(k), s, 720 * ease_in_out(k))
    if k > 0.8:
        c = Image.blend(c, nxt, clamp((k - 0.8) / 0.2))
    return c


# --------------------------------------------------------------------------- 6. agent chat -> card flip
def squash(img, sx):
    w = max(1, int(W * sx))
    im = img.resize((w, H), Image.BILINEAR)
    out = blank(BLACK)
    shade = Image.new("RGB", (w, H), BLACK)
    im = Image.blend(im, shade, (1 - sx) * 0.5)
    out.paste(im, (int(W / 2 - w / 2), 0))
    return out


def seg_agent(u, nxt):
    c = base_scene(scene_agent2, u)
    fstart = SEGS[5][1] - 0.36
    if u < fstart:
        return c
    k = (u - fstart) / 0.36
    if k < 0.5:
        return squash(c, 1 - ease_in(k * 2))
    return squash(nxt, ease_out_cubic((k - 0.5) * 2))


# --------------------------------------------------------------------------- 7. comments -> spin collapse
def seg_comments(u):
    c = base_scene(scene_comments2, u + 0.15)
    cstart = SEGS[6][1] - 0.32
    if u < cstart:
        return c
    k = ease_in((u - cstart) / 0.32)
    out = blank(BLACK)
    small = c.resize((max(1, int(W * (1 - k))), max(1, int(H * (1 - k)))), Image.BILINEAR).convert("RGBA")
    small = small.rotate(200 * k, expand=True)
    out.paste(small, (int(W / 2 - small.width / 2), int(H / 2 - small.height / 2)), small)
    return out


def seg_end(u):
    c = base_scene(scene_end2, u)
    if u < 0.12:  # white burst as the logo lands
        c = Image.blend(c, blank(WHITE), 0.8 * (1 - u / 0.12))
    return c


# --------------------------------------------------------------------------- frame assembly
def render(t):
    for name, (start, length) in STARTS.items():
        if start <= t < start + length or name == "end":
            u = t - start
            break
    nxt_u0 = {
        "stop": lambda: base_scene(scene_dream, 0.25),
        "hiding": lambda: seg_strips(0.05, blank()),
        "strips": lambda: base_scene(scene_count2, 0.1),
        "count": lambda: base_scene(scene_agent2, 0.05),
        "agent": lambda: base_scene(scene_comments2, 0.15),
    }
    if name == "feed":
        img = seg_feed(u)
    elif name == "stop":
        img = seg_stop(u, nxt_u0["stop"]())
    elif name == "hiding":
        img = seg_hiding(u, nxt_u0["hiding"]())
    elif name == "strips":
        img = seg_strips(u, nxt_u0["strips"]())
    elif name == "count":
        img = seg_count(u, nxt_u0["count"]())
    elif name == "agent":
        img = seg_agent(u, nxt_u0["agent"]())
    elif name == "comments":
        img = seg_comments(u)
    else:
        img = seg_end(u)
    # short glitch burst right after each cut
    for nm, (s0, _) in STARTS.items():
        if nm != "feed" and 0 <= t - s0 < 0.08:
            img = glitch(img, 0.5 * (1 - (t - s0) / 0.08), int(t * 1000))
    a = np.asarray(img, dtype=np.float32) * base.VIGNETTE + base.GRAIN[int(t * FPS) % 4]
    return np.clip(a, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- soundtrack: phonk-ish, 140 BPM
SR = 44100
N = int(SR * DUR)
add, env_exp, noise, hp, note = base.add, base.env_exp, base.noise, base.hp, base.note


def bass808(freq, length, glide_to=None):
    n = int(length * SR)
    tt = np.arange(n) / SR
    f = np.full(n, freq) if glide_to is None else freq * (glide_to / freq) ** np.minimum(1, tt / 0.12)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.25 * np.sin(2 * ph)
    punch = np.sin(2 * np.pi * np.cumsum(60 + 140 * np.exp(-tt * 40)) / SR) * np.exp(-tt * 25)
    return np.tanh(2.2 * (x * env_exp(n, 0.5) + punch * 0.8)) * np.minimum(1, tt / 0.003)


def cowbell(freq, length=0.18):
    n = int(length * SR)
    tt = np.arange(n) / SR
    x = np.sign(np.sin(2 * np.pi * freq * tt)) + np.sign(np.sin(2 * np.pi * freq * 1.48 * tt))
    return hp(x) * env_exp(n, 0.06) * 0.35


def snare(seed):
    n = int(0.25 * SR)
    tt = np.arange(n) / SR
    body = np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 35)
    return (hp(noise(n, seed)) * env_exp(n, 0.07) + body * 0.6) * 0.8


def whoosh(length, up=True, seed=3):
    n = int(length * SR)
    tt = np.arange(n) / SR
    nz = noise(n, seed)
    # crude sweeping band: mix of raw and differentiated noise by sweep position
    pos = tt / length if up else 1 - tt / length
    x = nz * (1 - pos) * 0.4 + hp(nz) * pos
    return x * np.sin(np.pi * tt / length) ** 2 * 0.6


def impact():
    n = int(1.0 * SR)
    tt = np.arange(n) / SR
    return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(38 + 90 * np.exp(-tt * 18)) / SR) * env_exp(n, 0.35)) + 0.3 * hp(noise(n, 4)) * np.exp(-tt * 30)


def stutter(buf, start, slice_len, repeats, gain):
    i = int(start * SR)
    n = int(slice_len * SR)
    seg = buf[i:i + n].copy()
    for r in range(repeats):
        j = i + r * n
        buf[j:j + n] = seg * gain


def build_audio():
    L = np.zeros(N)
    drop = STARTS["stop"][0]
    # intro: dull "office" pad under the boring feed, then it bitcrushes
    n_in = int(drop * SR)
    tt = np.arange(n_in) / SR
    pad = sum(np.sin(2 * np.pi * f * tt) for f in (220, 277.2, 329.6)) * 0.08
    L[:n_in] += pad
    add(L, 0.75, impact(), 0.45)  # "BORING." stamp
    add(L, 1.2, whoosh(0.8, True), 0.9)  # riser into the drop
    # E minor phonk: 808 roots per bar, cowbell riff in 16ths
    roots = [41.2, 41.2, 49.0, 36.7]  # E1 E1 G1 D1
    riff = [659.3, 0, 784.0, 659.3, 0, 587.3, 659.3, 0, 784.0, 0, 880.0, 784.0, 659.3, 0, 587.3, 0]
    beat = 0
    t = drop
    while t < DUR - 1.6:
        bar = beat // 4
        pos = beat % 4
        if pos in (0, 2) or (pos == 3 and bar % 2):
            glide = roots[(bar + 1) % 4] if pos == 3 else None
            add(L, t, bass808(roots[bar % 4] * 2, B * (1.4 if pos != 3 else 0.9), glide and glide * 2), 0.55)
        if pos == 2:
            add(L, t, snare(beat), 0.55)
        for h in range(4):  # cowbell riff
            f = riff[(pos * 4 + h) % 16]
            if f:
                add(L, t + h * B / 4, cowbell(f), 0.5)
        hats = 8 if bar % 2 else 4  # hat rolls every other bar
        for h in range(hats):
            add(L, t + h * B / hats, base.hat(beat * 8 + h, 0.03), 0.45)
        beat += 1
        t += B
    # transition sounds on every cut
    for name, (s0, _) in STARTS.items():
        if name in ("feed",):
            continue
        add(L, s0 - 0.35, whoosh(0.4, True, int(s0 * 10)), 0.6)
        add(L, s0, impact(), 0.35)
    add(L, drop, impact(), 0.6)
    # end: hard stop then a final 808 + cowbell sting
    end0 = STARTS["end"][0]
    L[int((end0 - 0.05) * SR):int(end0 * SR)] *= 0.2
    add(L, end0, bass808(82.4, 1.6), 0.7)
    for j, f in enumerate((659.3, 784.0, 987.8)):
        add(L, end0 + j * 0.09, cowbell(f, 0.4), 0.6)
    # glitch stutter while the feed tears
    stutter(L, 1.45, 0.045, 10, 0.9)
    R = np.roll(L, int(0.01 * SR)) * 0.95
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
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", WAV, "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", raw]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frames = int(DUR * FPS)
    for i in range(frames):
        proc.stdin.write(render(i / FPS).tobytes())
        if i % 90 == 0:
            print(f"frame {i}/{frames}", flush=True)
    proc.stdin.close()
    proc.wait()
    # second pass: Instagram-friendly size
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-c:v", "libx264", "-preset", "slow", "-crf", "22",
                    "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", OUT], check=True)
    os.remove(raw)
    print("done:", OUT)


if __name__ == "__main__":
    main()
