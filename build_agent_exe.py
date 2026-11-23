"""Empaquetador del Agente de Laptop Creditech by indatech. en un ejecutable único (.exe).

Genera:
1. El icono oficial `.ico` de `indatech.` (`shared/assets/indatech.ico`).
2. El ejecutable independiente `dist/Creditech_Instalador_Laptop.exe` que no requiere
   tener Python instalado en las laptops de los clientes.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt6.QtCore import QBuffer, QIODevice
from PyQt6.QtWidgets import QApplication

from agent.ui import render_indatech_logo_pixmap


def generate_ico_file(output_path: Path) -> Path:
    app = QApplication.instance() or QApplication([])
    pix = render_indatech_logo_pixmap(size=256, show_text=False, bg_color="#FFFFFF")

    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.ReadWrite)
    pix.save(buf, "PNG")
    png_bytes = bytes(buf.data())

    import io

    img = Image.open(io.BytesIO(png_bytes))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(
        output_path,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)],
    )
    return output_path


def build_exe() -> int:
    root = Path(__file__).resolve().parent
    ico_path = generate_ico_file(root / "shared" / "assets" / "indatech.ico")
    print(f"Icono generado en: {ico_path}")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "Creditech_Instalador_Laptop",
        "--icon",
        str(ico_path),
        "--exclude-module",
        "PyQt5",
        "--exclude-module",
        "fastapi",
        "--exclude-module",
        "uvicorn",
        "--exclude-module",
        "sqlalchemy",
        "--exclude-module",
        "xlsxwriter",
        "--exclude-module",
        "PIL",
        "--exclude-module",
        "numpy",
        str(root / "run_agent.py"),
    ]
    print("Compilando ejecutable .exe con PyInstaller...")
    res = subprocess.run(cmd, cwd=str(root))
    return res.returncode


if __name__ == "__main__":
    raise SystemExit(build_exe())
