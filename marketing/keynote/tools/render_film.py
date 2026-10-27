"""Render film.html with Playwright: 4 subframes per frame at 60 fps (240 samples/s), blended with ffmpeg tmix.

Usage:  python render_film.py [--workers 4] [--start 0] [--end 27]
Frames go to build/frames/f_XXXXX.jpg (index = round(t*240)); existing frames are skipped, so a run can resume.
"""
import argparse
import asyncio
import functools
import http.server
import os
import subprocess
import threading
import time

from playwright.async_api import async_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FR = os.path.join(ROOT, "build", "frames")
PORT = 8793
SUB = 240


def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    h.log_message = lambda *a: None
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), h).serve_forever()


async def worker(browser, indices, done):
    page = await browser.new_page(viewport={"width": 1080, "height": 1920})
    page.on("pageerror", lambda e: print("pageerror:", e))
    await page.goto(f"http://127.0.0.1:{PORT}/film.html")
    await page.evaluate("window.ready")
    frame = page.locator("#frame")
    for n in indices:
        path = os.path.join(FR, f"f_{n:05d}.jpg")
        if os.path.exists(path):
            done[0] += 1
            continue
        await page.evaluate(f"seek({n / SUB})")
        await frame.screenshot(path=path, type="jpeg", quality=93, timeout=60000)  # fail loudly instead of hanging
        done[0] += 1
    await page.close()


async def render(workers, start, end):
    threading.Thread(target=serve, daemon=True).start()
    os.makedirs(FR, exist_ok=True)
    # only frames not on disk yet, split evenly across workers (a resumed run stays parallel)
    idx = [n for n in range(int(start * SUB), int(end * SUB)) if not os.path.exists(os.path.join(FR, f"f_{n:05d}.jpg"))]
    done = [0]
    t0 = time.time()
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        tasks = [asyncio.create_task(worker(browser, idx[k::workers], done)) for k in range(workers)]
        while not all(t.done() for t in tasks):
            await asyncio.sleep(20)
            el = time.time() - t0
            rate = done[0] / max(el, 1)
            print(f"{done[0]}/{len(idx)} frames, {rate:.1f}/s, eta {(len(idx) - done[0]) / max(rate, 0.01) / 60:.1f} min", flush=True)
        await asyncio.gather(*tasks)
        await browser.close()


def encode():
    out = os.path.join(ROOT, "camouroles_find_film.mp4")
    vid = os.path.join(ROOT, "build", "video_60.mp4")
    # average every 4 consecutive subframes into one 60 fps frame (motion blur), keep each 4th
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(SUB), "-i", os.path.join(FR, "f_%05d.jpg"),
                    "-vf", "tmix=frames=4,select='eq(mod(n\\,4)\\,3)',setpts=N/60/TB", "-r", "60",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", vid], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vid, "-i", os.path.join(ROOT, "build", "soundtrack.wav"),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("done:", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--end", type=float, default=27.0)
    ap.add_argument("--encode-only", action="store_true")
    a = ap.parse_args()
    if not a.encode_only:
        asyncio.run(render(a.workers, a.start, a.end))
    if a.end >= 27.0 or a.encode_only:
        encode()
