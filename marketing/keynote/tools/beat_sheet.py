"""Render one frame per beat (at beat + offset) and tile them into contact sheets."""
import asyncio, functools, http.server, os, sys, threading
from PIL import Image, ImageDraw
from playwright.async_api import async_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PORT = 8792


def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    h.log_message = lambda *a: None
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), h).serve_forever()


async def main(offset, beats):
    threading.Thread(target=serve, daemon=True).start()
    out = os.path.join(ROOT, "check"); os.makedirs(out, exist_ok=True)
    async with async_playwright() as p:
        br = await p.chromium.launch()
        pg = await br.new_page(viewport={"width": 1080, "height": 1920})
        pg.on("pageerror", lambda e: print("pageerror:", e))
        pg.on("console", lambda m: print("console:", m.text) if m.type == "error" else None)
        await pg.goto(f"http://127.0.0.1:{PORT}/film.html"); await pg.evaluate("window.ready")
        shots = []
        for b in beats:
            t = (b + offset) * 0.5
            await pg.evaluate(f"seek({t})")
            f = os.path.join(out, f"b{b:02d}.jpg")
            await pg.locator("#frame").screenshot(path=f, type="jpeg", quality=80)
            shots.append((b, f))
        await br.close()
    per = 9
    for s in range(0, len(shots), per):
        grp = shots[s:s + per]
        sheet = Image.new("RGB", (len(grp) * 240, 450), "white"); d = ImageDraw.Draw(sheet)
        for i, (b, f) in enumerate(grp):
            sheet.paste(Image.open(f).resize((240, 427)), (i * 240, 0)); d.text((i * 240 + 6, 430), f"beat {b}", fill="black")
        sheet.save(os.path.join(out, f"sheet_{s // per}.jpg"), quality=85)
    print("ok", len(shots))


if __name__ == "__main__":
    off = float(sys.argv[1]) if len(sys.argv) > 1 else 0.45
    asyncio.run(main(off, list(range(54))))
