"""Render approval stills from film.html at given times. Usage: python render_stills.py 1.6 9.0 16.0 22.6"""
import asyncio
import functools
import http.server
import os
import sys
import threading

from playwright.async_api import async_playwright

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "stills")
PORT = 8791


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    handler.log_message = lambda *a: None
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler).serve_forever()


async def main(times):
    threading.Thread(target=serve, daemon=True).start()
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})
        page.on("console", lambda m: print("console:", m.text) if m.type in ("error", "warning") else None)
        page.on("pageerror", lambda e: print("pageerror:", e))
        await page.goto(f"http://127.0.0.1:{PORT}/film.html")
        await page.evaluate("window.ready")
        for t in times:
            await page.evaluate(f"seek({t})")
            path = os.path.join(OUT, f"still_{t:05.2f}.png")
            await page.locator("#frame").screenshot(path=path)
            print("saved", path)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main([float(x) for x in sys.argv[1:]] or [1.6, 9.0, 16.0, 22.6]))
