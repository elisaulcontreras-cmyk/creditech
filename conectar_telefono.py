"""Muestra la dirección Pública en Internet (4G/5G/Datos Móviles) y un Código QR para tu Teléfono.

Levanta automáticamente un Túnel Público Seguro (HTTPS) para que puedas abrir e instalar
la App de Creditech en tu teléfono celular y usarla desde CUALQUIER LUGAR (con datos móviles
o en otra red, sin tener que estar en el mismo Wi-Fi).
"""

from __future__ import annotations

import re
import socket
import subprocess
import sys
import threading
from pathlib import Path

import httpx
import qrcode
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from agent.ui import CREDITECH_QSS, IndatechLogoWidget, render_indatech_logo_pixmap


CLOUDFLARED_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
)


def get_local_lan_ip() -> str:
    """Detecta la dirección IP local (Wi-Fi / LAN) de esta computadora."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def make_qr_pixmap(url: str, size: int = 240) -> QPixmap:
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    pil_img = qr.make_image(fill_color="#071D20", back_color="#FFFFFF").convert("RGB")
    data = pil_img.tobytes("raw", "RGB")
    qimg = QImage(
        data,
        pil_img.size[0],
        pil_img.size[1],
        pil_img.size[0] * 3,
        QImage.Format.Format_RGB888,
    )
    return QPixmap.fromImage(qimg).scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def ensure_cloudflared_binary() -> Path:
    """Descarga `cloudflared.exe` automáticamente si no existe aún en la carpeta tools."""
    tools_dir = Path(__file__).resolve().parent / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    exe_path = tools_dir / "cloudflared.exe"
    if exe_path.exists() and exe_path.stat().st_size > 5_000_000:
        return exe_path

    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        with client.stream("GET", CLOUDFLARED_URL) as r:
            r.raise_for_status()
            with open(exe_path, "wb") as f:
                for chunk in r.iter_bytes(chunk_size=65536):
                    f.write(chunk)
    return exe_path


class PhoneConnectDialog(QDialog):
    tunnel_ready = pyqtSignal(str)
    tunnel_status = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Creditech by indatech. — Acceso desde Cualquier Red (4G / 5G / Wi-Fi)")
        self.setWindowIcon(QIcon(render_indatech_logo_pixmap(64, show_text=False)))
        self.setFixedWidth(520)
        self.setStyleSheet(CREDITECH_QSS)
        self._tunnel_proc: subprocess.Popen | None = None

        ip = get_local_lan_ip()
        self.lan_url = f"http://{ip}:8085"
        self.public_url = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        header = QFrame()
        header.setObjectName("headerBanner")
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 14, 16, 14)
        h_lay.addWidget(IndatechLogoWidget(size=56, show_text=True))
        t_col = QVBoxLayout()
        t_lbl = QLabel("Conectar Teléfono (Sin Mismo Wi-Fi)")
        t_lbl.setObjectName("brandTitle")
        t_lbl.setStyleSheet("color:#FFFFFF; font-size:18px; font-weight:900;")
        s_lbl = QLabel("Usa Datos Móviles (4G/5G) o cualquier red desde tu celular")
        s_lbl.setObjectName("brandSub")
        t_col.addWidget(t_lbl)
        t_col.addWidget(s_lbl)
        h_lay.addLayout(t_col, 1)
        layout.addWidget(header)

        card = QFrame()
        card.setObjectName("card")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(20, 18, 20, 18)
        c_lay.setSpacing(10)
        c_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_badge = QLabel("⏳ Activando enlace público gratuito por Internet (HTTPS)...")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setWordWrap(True)
        self.status_badge.setStyleSheet(
            "font-size: 12.5px; font-weight: 800; color: #D97706; "
            "background: #FFFBEB; padding: 8px; border-radius: 8px; border: 1px solid #FDE68A;"
        )
        c_lay.addWidget(self.status_badge)

        self.qr_lbl = QLabel()
        self.qr_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_lbl.setPixmap(make_qr_pixmap(self.lan_url, 230))
        c_lay.addWidget(self.qr_lbl)

        self.url_lbl = QLabel(f"Wi-Fi Local: {self.lan_url}")
        self.url_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.url_lbl.setWordWrap(True)
        self.url_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.url_lbl.setStyleSheet(
            "font-size: 14px; font-weight: 900; color: #008F64; "
            "background: #E6FBF4; padding: 10px; border-radius: 10px; border: 1px solid #99F3D6;"
        )
        c_lay.addWidget(self.url_lbl)

        help_lbl = QLabel(
            "• Con el enlace HTTPS que aparece arriba, puedes entrar desde tu teléfono\n"
            "  con DATOS MÓVILES (4G/5G) desde la calle sin estar en el mismo Wi-Fi.\n"
            "• Además, una vez abras la App en tu celular, el botón '🔑 PIN Cédula'\n"
            "  funciona en tu teléfono incluso si apagas esta PC o no tienes internet."
        )
        help_lbl.setWordWrap(True)
        help_lbl.setStyleSheet("font-size: 12px; color: #526B70;")
        c_lay.addWidget(help_lbl)

        layout.addWidget(card)

        close_btn = QPushButton("Cerrar")
        close_btn.setObjectName("primaryBtn")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.tunnel_ready.connect(self._on_tunnel_url)
        self.tunnel_status.connect(self._on_tunnel_status)

        threading.Thread(target=self._start_public_tunnel, daemon=True).start()

    def _on_tunnel_status(self, msg: str) -> None:
        self.status_badge.setText(msg)

    def _on_tunnel_url(self, pub_url: str) -> None:
        self.public_url = pub_url
        self.status_badge.setText("🌐 ¡ENLACE DE INTERNET ACTIVO! Escanea el QR con Datos Móviles (4G/5G)")
        self.status_badge.setStyleSheet(
            "font-size: 12.5px; font-weight: 900; color: #008F64; "
            "background: #E6FBF4; padding: 8px; border-radius: 8px; border: 1px solid #00D094;"
        )
        self.qr_lbl.setPixmap(make_qr_pixmap(pub_url, 230))
        self.url_lbl.setText(f"Internet (Cualquier Red 4G/5G):\n{pub_url}")

    def _start_public_tunnel(self) -> None:
        try:
            self.tunnel_status.emit("⏳ Preparando túnel de Internet Cloudflare (100% gratis)...")
            exe = ensure_cloudflared_binary()
            self.tunnel_status.emit("⏳ Conectando servidor local a Internet público HTTPS...")
            proc = subprocess.Popen(
                [str(exe), "tunnel", "--url", "http://localhost:8085", "--no-autoupdate"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self._tunnel_proc = proc
            pattern = re.compile(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com")
            assert proc.stdout is not None
            for line in proc.stdout:
                m = pattern.search(line)
                if m:
                    url = m.group(0)
                    Path("url_publica_telefono.txt").write_text(url, encoding="utf-8")
                    self.tunnel_ready.emit(url)
                    break
        except Exception as exc:
            self.tunnel_status.emit(f"Usando red local ({exc})")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = PhoneConnectDialog()
    dlg.exec()

