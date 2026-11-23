"""Genera la carpeta `docs/` lista para publicar como App PWA fija 24/7 en GitHub Pages."""

from __future__ import annotations

import json
from pathlib import Path

from server.dashboard import DASHBOARD_HTML
from shared.branding import INDATECH_LOGO_SVG


def build_docs() -> None:
    d = Path(__file__).resolve().parent / "docs"
    d.mkdir(parents=True, exist_ok=True)

    html = (
        DASHBOARD_HTML.replace('href="/manifest.json"', 'href="manifest.json"')
        .replace('href="/icon.svg"', 'href="icon.svg"')
        .replace("register('/sw.js')", "register('sw.js')")
    )
    (d / "index.html").write_text(html, encoding="utf-8")
    (d / "icon.svg").write_text(INDATECH_LOGO_SVG, encoding="utf-8")
    (d / "manifest.json").write_text(
        json.dumps(
            {
                "name": "Creditech by indatech.",
                "short_name": "Creditech",
                "description": "App de Control de Laptops Financiadas, PINs por Cédula y Excel de Deudores",
                "start_url": "./",
                "display": "standalone",
                "background_color": "#071D20",
                "theme_color": "#071D20",
                "icons": [
                    {
                        "src": "icon.svg",
                        "sizes": "any",
                        "type": "image/svg+xml",
                        "purpose": "any maskable",
                    }
                ],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (d / "sw.js").write_text(
        "self.addEventListener('install', (e) => self.skipWaiting());\n"
        "self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));\n",
        encoding="utf-8",
    )
    print(f"Carpeta docs/ generada en: {d}")


if __name__ == "__main__":
    build_docs()
