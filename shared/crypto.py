"""Criptografía y códigos de desbloqueo offline para Creditech.

Permite que el servidor genere un PIN numérico/alfanumérico corto de 8 dígitos
para desbloquear una laptop sin conexión a internet, y que la laptop verifique
el PIN usando su `device_secret` y la `cedula` del cliente.

También soporta un PIN de desbloqueo por cuota específica o por fecha, y evita
la reutilización (replay) del mismo PIN guardando un contador o nonce.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import date, timedelta


def generate_device_secret(cedula: str = "", master_key: str = "") -> str:
    """Genera el secreto de una laptop.

    Si se proporciona `cedula` (y opcionalmente `master_key`), deriva de forma
    determinista el secreto con HMAC-SHA256 para que la App Móvil del vendedor
    pueda generar PINs de desbloqueo desde su teléfono con solo ingresar la cédula
    del cliente, sin necesidad de estar en el mismo Wi-Fi ni conectarse al servidor.
    """
    if cedula and cedula.strip():
        import os

        key = (master_key or os.environ.get("CREDITECH_MASTER_KEY") or "INDATECH-CREDITECH-MASTER-2026").encode("utf-8")
        norm = _normalize_cedula(cedula)
        return hmac.new(key, f"DEVICE_SECRET|v1|{norm}".encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    return secrets.token_hex(16)


def generate_enrollment_code() -> str:
    """Genera un código de instalación/vinculación fácil de escribir (ej: CRD-4829-9104)."""
    p1 = secrets.randbelow(9000) + 1000
    p2 = secrets.randbelow(9000) + 1000
    return f"CRD-{p1}-{p2}"


def _normalize_cedula(cedula: str) -> str:
    """Normaliza la cédula quitando espacios, puntos y guiones, en mayúsculas."""
    return "".join(ch for ch in (cedula or "").upper() if ch.isalnum())


def generate_offline_pin(
    device_secret: str,
    cedula: str,
    unlock_days: int = 30,
    reference_date: date | None = None,
    installment_number: int = 0,
) -> str:
    """Genera un PIN de desbloqueo offline firmado con HMAC-SHA256.

    Formato del PIN: `DD-XXXXXX` (donde DD son los días de desbloqueo en 2 dígitos,
    o `99` para desbloqueo definitivo/permanente, y `XXXXXX` son 6 dígitos
    derivados del HMAC sobre `device_secret`, `cedula`, `reference_date`, `unlock_days`
    e `installment_number`).

    Parámetros:
        device_secret: Secreto compartido único de la laptop.
        cedula: Número de cédula del cliente.
        unlock_days: Días de desbloqueo (1..98, o 99 = liberación total/sin bloqueo).
        reference_date: Fecha de emisión del PIN (por defecto hoy).
        installment_number: Número de cuota pagada (0 = desbloqueo general).
    """
    ref = (reference_date or date.today()).isoformat()
    days_clamped = max(1, min(99, int(unlock_days)))
    prefix = f"{days_clamped:02d}"
    norm_id = _normalize_cedula(cedula)
    payload = f"CREDITECH|v1|{norm_id}|{ref}|{prefix}|{int(installment_number)}"
    digest = hmac.new(
        device_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    # Convertir los primeros 8 caracteres hex a un entero de 6 dígitos decimales
    numeric_code = int(digest[:8], 16) % 1_000_000
    return f"{prefix}-{numeric_code:06d}"


def verify_offline_pin(
    pin: str,
    device_secret: str,
    cedula: str,
    reference_date: date | None = None,
    max_installments: int = 36,
    used_pins: list[str] | set[str] | None = None,
) -> dict:
    """Verifica un PIN de desbloqueo offline en la laptop del cliente.

    Acepta PINs emitidos en la fecha de referencia (`reference_date`), ayer o mañana
    (para tolerar pequeñas diferencias de reloj o zona horaria) y para cualquier
    número de cuota entre 0 y `max_installments`.

    Retorna:
        {
            "valid": bool,
            "unlock_days": int,       # 99 significa liberación definitiva
            "permanent": bool,
            "installment_number": int | None,
            "normalized_pin": str,
            "reason": str,
        }
    """
    raw = (pin or "").strip().upper().replace(" ", "")
    if "-" not in raw and len(raw) == 8 and raw.isdigit():
        raw = f"{raw[:2]}-{raw[2:]}"

    parts = raw.split("-")
    if len(parts) != 2 or len(parts[0]) != 2 or len(parts[1]) != 6:
        return {
            "valid": False,
            "unlock_days": 0,
            "permanent": False,
            "installment_number": None,
            "normalized_pin": raw,
            "reason": "Formato inválido. Use el formato DD-XXXXXX (8 dígitos).",
        }

    if not (parts[0].isdigit() and parts[1].isdigit()):
        return {
            "valid": False,
            "unlock_days": 0,
            "permanent": False,
            "installment_number": None,
            "normalized_pin": raw,
            "reason": "El PIN solo debe contener números (formato DD-XXXXXX).",
        }

    used = set(used_pins or [])
    if raw in used:
        return {
            "valid": False,
            "unlock_days": 0,
            "permanent": False,
            "installment_number": None,
            "normalized_pin": raw,
            "reason": "Este PIN ya fue utilizado anteriormente en este equipo.",
        }

    unlock_days = int(parts[0])
    base_date = reference_date or date.today()
    candidate_dates = [
        base_date,
        base_date - timedelta(days=1),
        base_date + timedelta(days=1),
    ]

    for cand_date in candidate_dates:
        for inst_num in range(0, max_installments + 1):
            expected = generate_offline_pin(
                device_secret=device_secret,
                cedula=cedula,
                unlock_days=unlock_days,
                reference_date=cand_date,
                installment_number=inst_num,
            )
            if hmac.compare_digest(raw, expected):
                return {
                    "valid": True,
                    "unlock_days": unlock_days,
                    "permanent": unlock_days == 99,
                    "installment_number": inst_num,
                    "normalized_pin": raw,
                    "reason": "PIN verificado correctamente.",
                }

    return {
        "valid": False,
        "unlock_days": 0,
        "permanent": False,
        "installment_number": None,
        "normalized_pin": raw,
        "reason": "PIN incorrecto o vencido para la cédula y equipo registrados.",
    }
