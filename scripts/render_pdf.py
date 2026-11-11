#!/usr/bin/env python3
"""render_pdf.py: genera un PDF por pestaña del reporte con Chromium (Playwright).

Escribe pdf/<pestaña>.pdf (resumen, atun-pan, buena-mesa, donkat, aunt-jemima).
El botón "Descargar PDF" del reporte apunta al PDF de la pestaña abierta.
Cada PDF es una sola página larga con el ancho de escritorio, igual a como se ve en pantalla.

Uso:
    python scripts/render_pdf.py
"""
import functools
import http.server
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WIDTH = 1280


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:
        pass


def serve() -> tuple[http.server.ThreadingHTTPServer, int]:
    handler = functools.partial(QuietHandler, directory=str(ROOT))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def main() -> None:
    srv, port = serve()
    out = ROOT / "pdf"
    out.mkdir(exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": WIDTH, "height": 900})
            page.goto(f"http://127.0.0.1:{port}/", wait_until="networkidle")
            tabs = page.evaluate("() => window.REPORT_TABS")
            for slug in tabs:
                page.goto(f"http://127.0.0.1:{port}/#{slug}", wait_until="networkidle")
                page.evaluate("() => document.fonts.ready")
                page.emulate_media(media="print")
                h = page.evaluate("() => Math.ceil(document.documentElement.scrollHeight)")
                page.pdf(path=str(out / f"{slug}.pdf"), width=f"{WIDTH}px", height=f"{h + 2}px",
                         print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
                page.emulate_media(media="screen")
                print(f"  ✓ pdf/{slug}.pdf")
            browser.close()
    finally:
        srv.shutdown()


if __name__ == "__main__":
    main()
