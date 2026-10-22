"""CamouRoles reel #1 — 15 s, 9:16, kinetic type, synced 128 BPM soundtrack.

Run:  python make_reel.py      ->  camouroles_reel_01.mp4 next to this file
Everything (frames + music) is generated here; no stock assets except the brand logo.
"""
import math
import os
import random
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = os.path.join(HERE, "..", "..", "static", "logo-maroon.png")
OUT = os.path.join(HERE, "camouroles_reel_01.mp4")
WAV = os.path.join(HERE, "soundtrack.wav")

W, H, FPS, DUR = 1080, 1920, 30, 15.0
BPM = 128
B = 60 / BPM  # one beat in seconds

FONTS = "C:/Windows/Fonts/"
F_IMPACT = FONTS + "impact.ttf"
F_BLACK = FONTS + "seguibl.ttf"
F_BLACK_I = FONTS + "seguibli.ttf"
F_ERAS = FONTS + "ERASBD.TTF"
F_ROCK = FONTS + "ROCKEB.TTF"
F_BERLIN = FONTS + "BRLNSDB.TTF"
F_MONO = FONTS + "consolab.ttf"
F_BOLD = FONTS + "segoeuib.ttf"

PINK, LIME, CYAN, VIOLET = (255, 46, 147), (198, 255, 0), (0, 229, 255), (124, 77, 255)
ORANGE, YELLOW, BLUE, RED = (255, 109, 0), (255, 230, 0), (41, 98, 255), (255, 59, 48)
BLACK, WHITE, GOLD, CREAM = (10, 10, 12), (255, 255, 255), (232, 190, 92), (255, 244, 214)

# Scene boundaries, in beats
S1, S2, S3, S4, S5, S6, S7, S8, END = 0, 2, 4, 10, 13, 18, 21, 25, 32


# --------------------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_out_back(x, s=1.9):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def ease_in_out(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


# --------------------------------------------------------------------------- drawing helpers
_text_cache = {}


def text_img(txt, font, size, fill, stroke=0, stroke_fill=None):
    key = (txt, font, size, fill, stroke, stroke_fill)
    if key not in _text_cache:
        f = ImageFont.truetype(font, size)
        x0, y0, x1, y1 = f.getbbox(txt, stroke_width=stroke)
        im = Image.new("RGBA", (x1 - x0 + 24, y1 - y0 + 24), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((12 - x0, 12 - y0), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        _text_cache[key] = im
    return _text_cache[key]


def place(canvas, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale <= 0.02 or alpha <= 0.01:
        return
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    canvas.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


def glitch_text(canvas, txt, font, size, fill, cx, cy, scale=1.0, rot=0.0, split=10, stroke=0, stroke_fill=None, alpha=1.0):
    """Text with a cyan / magenta split behind it."""
    if split:
        place(canvas, text_img(txt, font, size, (0, 240, 255), stroke, stroke_fill), cx - split, cy, scale, rot, 0.85 * alpha)
        place(canvas, text_img(txt, font, size, (255, 0, 170), stroke, stroke_fill), cx + split, cy, scale, rot, 0.85 * alpha)
    place(canvas, text_img(txt, font, size, fill, stroke, stroke_fill), cx, cy, scale, rot, alpha)


def fit_size(txt, font, size, max_w):
    """Largest size up to `size` at which txt fits in max_w pixels."""
    w = ImageFont.truetype(font, size).getbbox(txt)[2]
    return size if w <= max_w else int(size * max_w / w)


def sticker(txt, bg, fg, size=54, font=F_BLACK, pad=(30, 16)):
    t = text_img(txt, font, size, fg)
    w, h = t.width + pad[0] * 2, t.height + pad[1] * 2
    im = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 12, w + 10, h + 12), radius=h // 2, fill=BLACK)  # hard drop shadow
    d.rounded_rectangle((4, 4, w + 4, h + 4), radius=h // 2, fill=bg, outline=BLACK, width=5)
    im.paste(t, (4 + pad[0], 4 + pad[1]), t)
    return im


def marquee(canvas, txt, color, y, offset, size=120, alpha=0.16):
    strip = text_img((txt + "   ") * 6, F_IMPACT, size, color)
    x = -(offset % (strip.width / 6)) + strip.width / 2
    place(canvas, strip, x, y, alpha=alpha)


def shake(u, start, length=0.18, amp=26, seed=1):
    if not (0 <= u - start < length):
        return 0, 0
    k = 1 - (u - start) / length
    rnd = random.Random(int((u - start) * 1000) + seed)
    return rnd.uniform(-amp, amp) * k, rnd.uniform(-amp, amp) * k


# --------------------------------------------------------------------------- scenes
LOGO_IMG = Image.open(LOGO).convert("RGBA")
LOGO_IMG = LOGO_IMG.resize((int(LOGO_IMG.width * 560 / LOGO_IMG.height), 560), Image.LANCZOS)
LOGO_GLOW = LOGO_IMG.filter(ImageFilter.GaussianBlur(40))

ROLES = [
    ("ROCKET", "ENGINEER"), ("DRONE", "AUTONOMY"), ("FUSION", "ENERGY"), ("QUANT", "RESEARCH"),
    ("ROBOTICS", ""), ("SATELLITE", "SOFTWARE"), ("EV", "BATTERIES"), ("CHIP", "DESIGN"),
    ("AI", "RESEARCH"), ("SPACE", "TECH"), ("NEURO", "TECH"), ("GAME", "ENGINES"),
    ("CLIMATE", "TECH"), ("FIRMWARE", ""), ("DEFENSE", "TECH"), ("BIOTECH", ""),
]
FLASH_BG = [PINK, LIME, BLUE, YELLOW, VIOLET, CYAN, RED, ORANGE, LIME, PINK, YELLOW, BLUE, ORANGE, VIOLET, RED, CYAN]
FLASH_FONTS = [F_IMPACT, F_BLACK, F_ERAS, F_ROCK, F_BERLIN, F_BLACK_I]


def ink_for(bg):
    return BLACK if sum(bg) > 420 else WHITE


def scene_stop(c, u):
    c.paste(PINK, (0, 0, W, H))
    marquee(c, "NOT ANOTHER JOB BOARD", WHITE, 300, u * 500)
    marquee(c, "NOT ANOTHER JOB BOARD", WHITE, 1650, -u * 500)
    dx, dy = shake(u, 0.12)
    s = 1 + 2.4 * (1 - ease_out_cubic(u / 0.16))
    glitch_text(c, "STOP", F_IMPACT, 430, WHITE, W / 2 + dx, 820 + dy, s, -4, split=14, stroke=10, stroke_fill=BLACK)
    if u >= B * 0.9:
        k = u - B * 0.9
        place(c, text_img("doom-scrolling", F_BLACK, 104, BLACK), W / 2, 1120, ease_out_back(k / 0.22))
        place(c, text_img("job boards", F_BLACK, 104, BLACK), W / 2, 1250, ease_out_back((k - 0.06) / 0.22))


def eyes(c, cx, cy, look):
    d = ImageDraw.Draw(c)
    for ex in (cx - 120, cx + 120):
        d.ellipse((ex - 95, cy - 95, ex + 95, cy + 95), fill=WHITE, outline=BLACK, width=10)
        px = ex + 40 * look
        d.ellipse((px - 42, cy - 30, px + 42, cy + 54), fill=BLACK)


def scene_hiding(c, u):
    c.paste(LIME, (0, 0, W, H))
    marquee(c, "PSST", BLACK, 260, u * 400, alpha=0.08)
    place(c, text_img("the fun jobs", F_BLACK, 132, BLACK), W / 2, 700, ease_out_back(u / 0.2), -3)
    if u >= B * 0.5:
        k = u - B * 0.5
        dx, dy = shake(k, 0, 0.14, 18, 3)
        glitch_text(c, "are HIDING", F_IMPACT, 210, BLACK, W / 2 + dx, 900 + dy, ease_out_back(k / 0.18), 3, split=8)
    if u >= B * 1.0:
        k = u - B * 1.0
        look = math.sin(k * 18) if k < 0.5 else -1
        eyes(c, W / 2, 1250 - 40 * (1 - ease_out_back(k / 0.2)), look)


def scene_flashes(c, u):
    i = min(11, int(u / (B / 2)))
    k = u - i * B / 2
    bg = FLASH_BG[i % len(FLASH_BG)]
    c.paste(bg, (0, 0, W, H))
    ink = ink_for(bg)
    marquee(c, "NICHE  NICHE  NICHE", ink, 220 + 60 * (i % 3), u * 900 * (1 if i % 2 else -1), 150, 0.1)
    rnd = random.Random(i * 7)
    rot = rnd.uniform(-7, 7)
    font = FLASH_FONTS[i % len(FLASH_FONTS)]
    s = 1 + 0.35 * (1 - ease_out_cubic(k / 0.09))
    top, bottom = ROLES[i]
    size = fit_size(max(top, bottom, key=len), font, 250, 820)
    if bottom:
        glitch_text(c, top, font, size, ink, W / 2, 820, s, rot, split=9)
        glitch_text(c, bottom, font, size, ink, W / 2, 820 + size * 1.02, s, rot, split=9)
    else:
        glitch_text(c, top, font, size, ink, W / 2, 920, s, rot, split=9)
    place(c, sticker("hiring now", BLACK if ink == BLACK else WHITE, WHITE if ink == BLACK else BLACK, 50), W / 2 + 230, 520, 1, 8 + 4 * math.sin(u * 20))
    place(c, text_img(f"{i + 1:02d}/12", F_MONO, 64, ink), W / 2, 1600, 1, 0, 0.7)


def scene_count(c, u):
    c.paste(VIOLET, (0, 0, W, H))
    marquee(c, "REAL OPENINGS", WHITE, 360, u * 450, 130, 0.1)
    n = int(10000 * ease_out_cubic(u / (B * 1.2)))
    dx, dy = shake(u, B * 1.2, 0.15, 20, 5)
    glitch_text(c, f"{n:,}+", F_IMPACT, 300, WHITE, W / 2 + dx, 760 + dy, 1, -2, split=10, stroke=8, stroke_fill=BLACK)
    if u >= B * 1.3:
        k = u - B * 1.3
        place(c, text_img("niche jobs", F_BLACK, 150, LIME, 6, BLACK), W / 2, 1020, ease_out_back(k / 0.2), 3)
    if u >= B * 2.0:
        k = u - B * 2.0
        a = ease_out_cubic(k / 0.15)
        place(c, text_img("straight from company", F_BOLD, 64, WHITE), W / 2, 1220, 1, 0, a)
        place(c, text_img("career pages", F_BOLD, 64, WHITE), W / 2, 1300, 1, 0, a)


def cv_card(t):
    im = Image.new("RGBA", (440, 560), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((16, 20, 436, 556), 34, fill=BLACK)
    d.rounded_rectangle((4, 4, 424, 540), 34, fill=WHITE, outline=BLACK, width=6)
    d.rounded_rectangle((40, 50, 140, 150), 22, fill=PINK)
    for j, w_ in enumerate((300, 340, 260, 320, 220, 300, 180)):
        d.rounded_rectangle((40, 190 + j * 46, 40 + w_, 214 + j * 46), 12, fill=(225, 225, 232))
    pdf = text_img("CV.pdf", F_BLACK, 54, BLACK)
    im.paste(pdf, (160, 70), pdf)
    return im


CV_CARD = cv_card(0)


def match_ring(c, cx, cy, pct):
    d = ImageDraw.Draw(c)
    r = 230
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=BLACK, width=46)
    d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * pct / 100, fill=PINK, width=46)
    place(c, text_img(f"{int(pct)}%", F_IMPACT, 170, BLACK), cx, cy - 18)
    place(c, text_img("match", F_BLACK, 56, BLACK), cx, cy + 95)


def chat_bubble(txt, bg, fg, max_chars=None, align="left"):
    shown = txt if max_chars is None else txt[:max_chars]
    t = text_img(shown or " ", F_BLACK, 62, fg)
    w, h = max(t.width + 56, 120), t.height + 40
    im = Image.new("RGBA", (w + 14, h + 14), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 12, w + 10, h + 12), 34, fill=BLACK)
    d.rounded_rectangle((2, 2, w + 2, h + 2), 34, fill=bg, outline=BLACK, width=5)
    im.paste(t, (30, 22), t)
    return im


def result_chip(title, meta):
    im = Image.new("RGBA", (900, 176), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 12, 896, 172), 30, fill=BLACK)
    d.rounded_rectangle((2, 2, 886, 162), 30, fill=WHITE, outline=BLACK, width=5)
    d.rounded_rectangle((26, 32, 122, 128), 22, fill=LIME, outline=BLACK, width=4)
    t = text_img(title, F_BLACK, 54, BLACK)
    im.paste(t, (146, 24), t)
    m = text_img(meta, F_BOLD, 42, (90, 90, 100))
    im.paste(m, (146, 94), m)
    return im


AGENT_ASK = "remote robotics, 2 yrs exp"
AGENT_REPLY = "On it. Found 37 that fit you"
CHIPS = [result_chip("Robotics Software Eng.", "Remote  ·  1–3 yrs"), result_chip("Autonomy Engineer", "Bengaluru  ·  2–4 yrs")]


def scene_agent(c, u):
    c.paste(BLUE, (0, 0, W, H))
    marquee(c, "AI AGENT  AI AGENT", WHITE, 300, u * 500, 130, 0.1)
    place(c, sticker("your AI job agent", LIME, BLACK, 76, F_BLACK), W / 2, 520, ease_out_back(u / 0.2), -3)
    # you type...
    typed = int(len(AGENT_ASK) * clamp((u - 0.15) / 0.55))
    if u >= 0.1:
        b = chat_bubble(AGENT_ASK, YELLOW, BLACK, typed)
        place(c, b, W - 60 - b.width / 2, 800)
    # ...it thinks...
    if 0.8 <= u < 1.1:
        d = ImageDraw.Draw(c)
        for j in range(3):
            r = 16 + 8 * max(0, math.sin((u * 14) - j))
            cx = 150 + j * 70
            d.ellipse((cx - r, 1010 - r, cx + r, 1010 + r), fill=WHITE)
    # ...and answers with real results
    if u >= 1.1:
        k = u - 1.1
        b = chat_bubble(AGENT_REPLY, WHITE, BLACK)
        place(c, b, 60 + b.width / 2, 1010, ease_out_back(k / 0.18))
        for j, chip in enumerate(CHIPS):
            kk = k - 0.2 - j * 0.16
            if kk > 0:
                place(c, chip, 60 + chip.width / 2, 1220 + j * 200 + 500 * (1 - ease_out_back(kk / 0.25, 1.3)), 1, (-1.5, 1.5)[j])
    if u >= 1.75:
        place(c, sticker("it actually talks back", PINK, WHITE, 56), W / 2 + 100, 1660, ease_out_back((u - 1.75) / 0.2), 6)


def scene_cv(c, u):
    c.paste(CYAN, (0, 0, W, H))
    marquee(c, "UPLOAD  UPLOAD", BLACK, 280, u * 500, 130, 0.08)
    if u < 0.62:
        place(c, text_img("drop your CV", F_BLACK, 140, BLACK), W / 2, 520, ease_out_back(u / 0.18), -3)
        y = 1080 + 700 * (1 - ease_out_back(u / 0.32, 1.4))
        place(c, CV_CARD, W / 2, y, 1, 8 * (1 - ease_out_cubic(u / 0.35)) - 3)
    else:
        k = u - 0.62
        place(c, text_img("AI ranks by", F_BLACK, 120, BLACK), W / 2, 460, ease_out_back(k / 0.15))
        dx, dy = shake(k, 0.08, 0.14, 16, 9)
        glitch_text(c, "YOUR FIT", F_IMPACT, 230, PINK, W / 2 + dx, 640 + dy, ease_out_back((k - 0.04) / 0.18), 3, split=8, stroke=8, stroke_fill=BLACK)
        match_ring(c, W / 2, 1180, 94 * ease_out_cubic((k - 0.08) / 0.5))


COMMENTS = [("aarav.codes", "rocket stuff fr", ORANGE), ("zoya.quant", "quant at 22??", VIOLET),
            ("kabir_builds", "drone engineer pls", LIME), ("meera.space", "anything in SPACE", CYAN)]


def comment(user, txt, color):
    im = Image.new("RGBA", (820, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 12, 816, 146), 30, fill=BLACK)
    d.rounded_rectangle((2, 2, 806, 136), 30, fill=WHITE, outline=BLACK, width=5)
    d.ellipse((24, 28, 104, 108), fill=color, outline=BLACK, width=4)
    u_ = text_img(user, F_BOLD, 34, (110, 110, 120))
    im.paste(u_, (126, 18), u_)
    t = text_img(txt, F_BLACK, 50, BLACK)
    im.paste(t, (126, 62), t)
    heart = text_img("♥", F_BLACK, 48, PINK)
    im.paste(heart, (740, 40), heart)
    return im


COMMENT_IMGS = [comment(*c_) for c_ in COMMENTS]


def scene_comments(c, u):
    c.paste(PINK, (0, 0, W, H))
    marquee(c, "COMMENT  COMMENT", WHITE, 250, u * 600, 130, 0.12)
    place(c, text_img("comment your", F_BLACK, 110, WHITE, 5, BLACK), W / 2, 430, ease_out_back(u / 0.18), -2)
    dx, dy = shake(u, 0.12, 0.15, 18, 13)
    glitch_text(c, "DREAM", F_IMPACT, 250, YELLOW, W / 2 + dx, 600 + dy, ease_out_back((u - 0.06) / 0.2), 3, split=10, stroke=9, stroke_fill=BLACK)
    place(c, text_img("niche job", F_BLACK, 110, WHITE, 5, BLACK), W / 2, 790, ease_out_back((u - 0.12) / 0.2), -1)
    for j, im in enumerate(COMMENT_IMGS):
        k = u - 0.35 - j * 0.22
        if k > 0:
            side = -1 if j % 2 else 1
            place(c, im, W / 2 + side * 30, 990 + j * 165, ease_out_back(k / 0.2, 2.2), side * 2)
    if u >= 1.5:
        y = 1700 + 18 * math.sin(u * 16)
        d = ImageDraw.Draw(c)
        d.polygon([(W / 2 - 60, y - 40), (W / 2 + 60, y - 40), (W / 2, y + 40)], fill=YELLOW, outline=BLACK)


PARTICLES = [(random.Random(s).uniform(0, 2 * math.pi), random.Random(s + 99).uniform(500, 1300),
              random.choice([PINK, LIME, CYAN, YELLOW, VIOLET, ORANGE]), random.Random(s + 7).uniform(10, 26)) for s in range(70)]


def logo_tile():
    """The brand logo on a black sticker tile with a lime rim and hard shadow."""
    size = 640
    im = Image.new("RGBA", (size + 40, size + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((24, 30, size + 24, size + 30), 90, fill=BLACK)            # hard shadow
    d.rounded_rectangle((4, 4, size + 4, size + 4), 90, fill=CREAM, outline=LIME, width=16)  # light tile so the maroon reads
    logo = LOGO_IMG.resize((int(LOGO_IMG.width * 470 / LOGO_IMG.height), 470), Image.LANCZOS)
    glow = logo.filter(ImageFilter.GaussianBlur(26))
    im.paste(logo, ((size + 8 - logo.width) // 2, (size + 8 - logo.height) // 2), logo)
    return im


LOGO_TILE = logo_tile()


def scene_end(c, u):
    c.paste(VIOLET, (0, 0, W, H))
    marquee(c, "NICHE JOBS  NICHE JOBS", WHITE, 230, u * 450, 130, 0.13)
    marquee(c, "NICHE JOBS  NICHE JOBS", WHITE, 1830, -u * 450, 130, 0.13)
    d = ImageDraw.Draw(c)
    for ang, speed, col, size in PARTICLES:  # confetti burst from the logo
        k = clamp(u / 1.2)
        dist = speed * ease_out_cubic(k)
        x = W / 2 + math.cos(ang) * dist
        y = 640 + math.sin(ang) * dist + 500 * k * k
        if k < 1:
            d.rectangle((x - size / 2, y - size / 2, x + size / 2, y + size / 2), fill=col if col != VIOLET else WHITE, outline=BLACK, width=3)
    s = ease_out_back(u / 0.35, 1.6)
    wobble = -4 + 2.5 * math.sin(u * 4)
    place(c, LOGO_TILE, W / 2, 660, s * 0.92, wobble)
    if u >= 0.25:
        k = u - 0.25
        glitch_text(c, "CAMOUROLES", F_IMPACT, 190, WHITE, W / 2, 1110, ease_out_back(k / 0.2), -2, split=9, stroke=9, stroke_fill=BLACK)
    if u >= 0.55:
        k = u - 0.55
        place(c, text_img("niche jobs. real openings.", F_BLACK, 62, WHITE, 4, BLACK), W / 2, 1250, ease_out_back(k / 0.2))
    if u >= 0.85:
        k = u - 0.85
        place(c, sticker("camouroles.pages.dev", LIME, BLACK, 60, F_BLACK), W / 2, 1390, ease_out_back(k / 0.22), 2)
    if u >= 1.25:
        k = u - 1.25
        bob = 8 * math.sin(u * 7)
        place(c, sticker("follow for daily niche drops", PINK, WHITE, 50), W / 2, 1545 + bob, ease_out_back(k / 0.2), -4)
    if u >= 1.75:
        k = u - 1.75
        place(c, sticker("save this", YELLOW, BLACK, 50), W / 2 + 250, 1690, ease_out_back(k / 0.2), 8)
        place(c, sticker("link in bio", CYAN, BLACK, 50), W / 2 - 230, 1700, ease_out_back((k - 0.1) / 0.2), -7)


SCENES = [(S1, scene_stop), (S2, scene_hiding), (S3, scene_flashes), (S4, scene_count),
          (S5, scene_agent), (S6, scene_cv), (S7, scene_comments), (S8, scene_end)]

rng = np.random.default_rng(7)
GRAIN = [rng.integers(-14, 15, (H, W, 1), dtype=np.int16) for _ in range(4)]
yy, xx = np.mgrid[0:H, 0:W]
VIGNETTE = (1 - 0.12 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2).clip(0, 1) ** 1.5)[..., None].astype(np.float32)


def render(t):
    beat = t / B
    start, fn = [s for s in SCENES if beat >= s[0]][-1]
    c = Image.new("RGB", (W, H), BLACK)
    fn(c, t - start * B)
    a = np.asarray(c, dtype=np.float32) * VIGNETTE
    # quick white flash on every scene cut
    for s, _ in SCENES[1:]:
        dt = t - s * B
        if 0 <= dt < 0.06:
            a = a + (255 - a) * (1 - dt / 0.06) * 0.55
    a = a + GRAIN[int(t * FPS) % 4]
    return np.clip(a, 0, 255).astype(np.uint8)


# --------------------------------------------------------------------------- soundtrack
SR = 44100
N = int(SR * DUR)


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (SR * tau))


def add(buf, start, sig, gain=1.0):
    i = int(start * SR)
    if i >= len(buf):
        return
    sig = sig[: len(buf) - i]
    buf[i: i + len(sig)] += sig * gain


def kick():
    n = int(0.35 * SR)
    tt = np.arange(n) / SR
    f = 45 + 110 * np.exp(-tt * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.12)


def noise(n, seed):
    return np.random.default_rng(seed).uniform(-1, 1, n)


def hp(x):
    return np.diff(x, prepend=0)


def clap(seed=1):
    n = int(0.22 * SR)
    x = hp(hp(noise(n, seed))) * env_exp(n, 0.05)
    for d in (0.008, 0.016):
        x[int(d * SR):] += x[: n - int(d * SR)] * 0.6
    return x * 0.5


def hat(seed=2, length=0.05):
    n = int(length * SR)
    return hp(hp(noise(n, seed))) * env_exp(n, 0.012) * 0.35


def note(freq, length, harm=(1, 0.5, 0.33, 0.25), tau=0.2):
    n = int(length * SR)
    tt = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * freq * (k + 1) * tt) for k, a in enumerate(harm))
    attack = np.minimum(1, tt / 0.004)
    return x * env_exp(n, tau) * attack


def riser(length):
    n = int(length * SR)
    tt = np.arange(n) / SR
    f = 200 * (8 ** (tt / length))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3
    nz = hp(noise(n, 5)) * 0.25
    return (tone + nz) * (tt / length) ** 2


def boom():
    n = int(0.9 * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 50 * tt) + 0.4 * hp(noise(n, 9)) * np.exp(-tt * 20)) * env_exp(n, 0.3)


def blip(freq):
    return note(freq, 0.09, (1, 0.3), 0.03)


def build_audio():
    L = np.zeros(N)
    # F minor-ish loop: Fm, Db, Ab, Eb  (one chord per bar)
    roots = [43.65, 34.65, 51.91, 38.89]
    chords = [(349.2, 415.3, 523.3), (277.2, 349.2, 415.3), (415.3, 523.3, 622.3), (311.1, 392.0, 466.2)]
    total_beats = int(DUR / B) + 1
    for bt in range(total_beats):
        t = bt * B
        bar = (bt // 4) % 4
        quiet = bt < S3 or bt >= S8 + 3
        if not (S2 - 0.01 < bt < S3):  # leave a gap before the drop
            add(L, t, kick(), 0.9 if not quiet else 0.6)
        if bt % 2 == 1 and S3 <= bt < S8:
            add(L, t, clap(bt), 0.7)
        if S3 <= bt < S8:
            for h in range(4 if S3 <= bt < S4 else 2):
                add(L, t + h * B / (4 if S3 <= bt < S4 else 2), hat(bt * 4 + h), 0.6)
            for h in range(2):  # off-beat sub bass
                add(L, t + B / 2 * h + B / 4, note(roots[bar] * 2, B / 2, (1, 0.6, 0.2), 0.15), 0.55)
        if S5 <= bt < S7:  # arp plucks
            for h in range(4):
                add(L, t + h * B / 4, note(chords[bar][h % 3] * 2, 0.15, (1, 0.25), 0.05), 0.12)
    # risers into the drop and into the end card
    add(L, S3 * B - 1.0, riser(1.0), 0.8)
    add(L, S8 * B - 0.8, riser(0.8), 0.7)
    # hits on scene cuts
    for s, _ in SCENES:
        add(L, s * B, boom(), 0.5)
    # a blip for every flash card, climbing in pitch
    for i in range(12):
        add(L, S3 * B + i * B / 2, blip(660 * 2 ** (i % 8 / 12)), 0.25)
    # counter ticks, then the "ding" when the match ring fills
    for i in range(12):
        add(L, S4 * B + i * B * 1.2 / 12, blip(1200), 0.12)
    for i in range(18):  # keyboard clicks while the question types out
        add(L, S5 * B + 0.15 + i * 0.03, hat(500 + i, 0.02), 0.5)
    add(L, S5 * B + 1.1, note(880, 0.25, (1, 0.3), 0.08), 0.3)  # message received
    add(L, S5 * B + 1.1, note(1318.5, 0.25, (1, 0.3), 0.08), 0.2)
    for j in range(4):  # comment pops
        add(L, S7 * B + 0.35 + j * 0.22, blip(880 * 2 ** (j / 6)), 0.3)
    add(L, S6 * B + 0.62 + 0.55, note(1318.5, 0.6, (1, 0.4, 0.2), 0.25), 0.35)
    add(L, S6 * B + 0.62 + 0.55, note(1975.5, 0.6, (1, 0.3), 0.25), 0.2)
    # end chord with a little echo
    end_chord = sum(note(f, 2.4, (1, 0.5, 0.25), 0.9) for f in (349.2, 415.3, 523.3, 698.5))
    for k, g in enumerate((0.35, 0.2, 0.12)):
        add(L, S8 * B + k * 0.18, end_chord, g)
    # stereo: tiny delay on the right for width, soft clip, fade out
    R = np.roll(L, int(0.012 * SR)) * 0.95
    st = np.stack([L, R], 1)
    st = np.tanh(st * 1.4) / np.tanh(1.4)
    fade = np.ones(N)
    fade[-int(0.4 * SR):] = np.linspace(1, 0, int(0.4 * SR))
    st *= fade[:, None] * 0.9
    with wave.open(WAV, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


# --------------------------------------------------------------------------- main
def main():
    build_audio()
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", WAV,
           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    frames = int(DUR * FPS)
    for i in range(frames):
        proc.stdin.write(render(i / FPS).tobytes())
        if i % 60 == 0:
            print(f"frame {i}/{frames}", flush=True)
    proc.stdin.close()
    proc.wait()
    print("done:", OUT)


if __name__ == "__main__":
    main()
