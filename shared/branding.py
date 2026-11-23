"""Activos visuales (Logo oficial Indatech / Creditech en SVG y QPixmap).

Renderiza el isotipo metaball en verde esmeralda (`#00D094`) y la marca
`indatech.` / `Creditech` para usarse tanto en el Panel Web del Servidor como
en la aplicación de escritorio PyQt6 (ventana del cliente, instalador,
aviso de pago y pantalla de bloqueo).
"""

from __future__ import annotations

import base64
from pathlib import Path


# SVG vectorial fiel al logo proporcionado: isotipo metaball orgánico en #00D094
# + tipografía geométrica bold "indatech."
INDATECH_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 420" width="100%" height="100%">
  <defs>
    <!-- Filtro gooey/metaball para que las uniones entre nodos sean curvas orgánicas idénticas al logo -->
    <filter id="goo" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="11" result="blur" />
      <feColorMatrix in="blur" mode="matrix"
        values="1 0 0 0 0
                0 1 0 0 0
                0 0 1 0 0
                0 0 0 24 -10" result="goo" />
      <feComposite in="SourceGraphic" in2="goo" operator="atop"/>
    </filter>
  </defs>

  <rect width="420" height="420" rx="48" fill="#FFFFFF"/>

  <!-- Isotipo metaball verde esmeralda (#00D094) -->
  <g fill="#00D094" filter="url(#goo)">
    <!-- Pieza superior en L invertida: (158,68) -> (236,68) -> (236,142) -->
    <circle cx="158" cy="68" r="28"/>
    <circle cx="236" cy="68" r="28"/>
    <circle cx="236" cy="142" r="26"/>
    <line x1="158" y1="68" x2="236" y2="68" stroke="#00D094" stroke-width="26" stroke-linecap="round"/>
    <line x1="236" y1="68" x2="236" y2="142" stroke="#00D094" stroke-width="26" stroke-linecap="round"/>

    <!-- Punto suelto arriba a la derecha -->
    <circle cx="312" cy="68" r="27"/>

    <!-- Punto suelto a la izquierda media -->
    <circle cx="92" cy="162" r="26"/>

    <!-- Pieza vertical media izquierda: (158,136) -> (158,212) -->
    <circle cx="158" cy="136" r="27"/>
    <circle cx="158" cy="212" r="27"/>
    <line x1="158" y1="136" x2="158" y2="212" stroke="#00D094" stroke-width="28" stroke-linecap="round"/>

    <!-- Pieza inferior escalonada: (158,278) -> (236,278) -> (236,214) -> (296,154) -->
    <circle cx="158" cy="278" r="28"/>
    <circle cx="236" cy="278" r="27"/>
    <circle cx="236" cy="214" r="26"/>
    <circle cx="296" cy="154" r="28"/>
    <line x1="158" y1="278" x2="236" y2="278" stroke="#00D094" stroke-width="24" stroke-linecap="round"/>
    <line x1="236" y1="278" x2="236" y2="214" stroke="#00D094" stroke-width="25" stroke-linecap="round"/>
    <line x1="236" y1="214" x2="296" y2="154" stroke="#00D094" stroke-width="26" stroke-linecap="round"/>

    <!-- Punto suelto abajo a la derecha -->
    <circle cx="302" cy="240" r="26"/>
  </g>

  <!-- Logotipo "indatech." -->
  <text x="210" y="378"
        text-anchor="middle"
        font-family="'Segoe UI', 'Inter', 'Arial Black', sans-serif"
        font-size="76"
        font-weight="900"
        letter-spacing="-2.5"
        fill="#00D094">indatech.</text>
</svg>
"""

# Versión compacta (solo el isotipo sobre fondo blanco/transparente) para iconos y avatares
INDATECH_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="45 20 315 300" width="100%" height="100%">
  <defs>
    <filter id="gooIcon" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur" />
      <feColorMatrix in="blur" mode="matrix"
        values="1 0 0 0 0
                0 1 0 0 0
                0 0 1 0 0
                0 0 0 24 -10" result="goo" />
      <feComposite in="SourceGraphic" in2="goo" operator="atop"/>
    </filter>
  </defs>
  <rect x="45" y="20" width="315" height="300" rx="54" fill="#FFFFFF"/>
  <g fill="#00D094" filter="url(#gooIcon)">
    <circle cx="158" cy="68" r="28"/>
    <circle cx="236" cy="68" r="28"/>
    <circle cx="236" cy="142" r="26"/>
    <line x1="158" y1="68" x2="236" y2="68" stroke="#00D094" stroke-width="26" stroke-linecap="round"/>
    <line x1="236" y1="68" x2="236" y2="142" stroke="#00D094" stroke-width="26" stroke-linecap="round"/>
    <circle cx="312" cy="68" r="27"/>
    <circle cx="92" cy="162" r="26"/>
    <circle cx="158" cy="136" r="27"/>
    <circle cx="158" cy="212" r="27"/>
    <line x1="158" y1="136" x2="158" y2="212" stroke="#00D094" stroke-width="28" stroke-linecap="round"/>
    <circle cx="158" cy="278" r="28"/>
    <circle cx="236" cy="278" r="27"/>
    <circle cx="236" cy="214" r="26"/>
    <circle cx="296" cy="154" r="28"/>
    <line x1="158" y1="278" x2="236" y2="278" stroke="#00D094" stroke-width="24" stroke-linecap="round"/>
    <line x1="236" y1="278" x2="236" y2="214" stroke="#00D094" stroke-width="25" stroke-linecap="round"/>
    <line x1="236" y1="214" x2="296" y2="154" stroke="#00D094" stroke-width="26" stroke-linecap="round"/>
    <circle cx="302" cy="240" r="26"/>
  </g>
</svg>
"""


def get_logo_data_uri(compact: bool = False) -> str:
    """Devuelve el logo en formato Data URI (`data:image/svg+xml;base64,...`) para HTML."""
    svg = INDATECH_ICON_SVG if compact else INDATECH_LOGO_SVG
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def ensure_logo_files() -> Path:
    """Guarda los archivos SVG del logo en `shared/assets/` y devuelve la carpeta."""
    assets_dir = Path(__file__).resolve().parent / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "indatech_logo.svg").write_text(INDATECH_LOGO_SVG, encoding="utf-8")
    (assets_dir / "indatech_icon.svg").write_text(INDATECH_ICON_SVG, encoding="utf-8")
    return assets_dir
