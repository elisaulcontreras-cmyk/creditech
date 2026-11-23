"""Almacenamiento local seguro y sincronización con el servidor para el Agente Creditech.

Permite que cada laptop financiada:
1. Guarde localmente los datos del cliente (Nombre y Número de Cédula), el modelo/serial,
   el `device_secret` para verificar PINs offline, y el cronograma completo de cuotas.
2. Evalúe localmente en todo momento (incluso si el cliente desconecta el Wi-Fi)
   si debe mostrar el **Aviso de Pago 1 día antes** del vencimiento o si debe
   **Bloquear el equipo** por cuota vencida.
3. Sincronice con el Servidor Central cada vez que haya conexión para recibir
   bloqueos/desbloqueos inmediatos o actualizaciones de pagos.
4. Valide códigos PIN offline firmados por el servidor y desbloquee el equipo.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import socket
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from shared.crypto import generate_device_secret, generate_enrollment_code, verify_offline_pin
from shared.policy import evaluate_device_policy, generate_installment_schedule, parse_iso_date


def get_hardware_fingerprint() -> tuple[str, str]:
    """Obtiene una huella única de hardware (MAC/Node + Hostname) de la laptop."""
    hostname = socket.gethostname() or platform.node() or "LAPTOP"
    node_hex = f"{uuid.getnode():012x}"
    digest = hashlib.sha256(f"{hostname}|{node_hex}|{platform.machine()}".encode("utf-8")).hexdigest()[:16].upper()
    return f"HW-{digest}", hostname


def get_agent_state_path() -> Path:
    """Ruta donde se guarda el estado local del agente en la laptop."""
    custom_dir = os.environ.get("CREDITECH_AGENT_DIR")
    if custom_dir:
        base = Path(custom_dir)
    else:
        local_appdata = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        base = Path(local_appdata) / "Creditech"
    base.mkdir(parents=True, exist_ok=True)
    return base / "agent_state.json"


class AgentStateManager:
    """Gestiona la configuración, caché offline, sincronización y PINs de la laptop."""

    def __init__(self, state_path: Path | str | None = None) -> None:
        self.state_path = Path(state_path) if state_path else get_agent_state_path()
        self.state: dict[str, Any] = self._load()

    def _default_state(self) -> dict[str, Any]:
        hw_id, hostname = get_hardware_fingerprint()
        default_url = os.environ.get(
            "CREDITECH_SERVER_URL", "https://creditech-indatech.onrender.com"
        )
        cfg_file = Path(__file__).resolve().parent.parent / "server_url.txt"
        if cfg_file.exists():
            try:
                txt = cfg_file.read_text(encoding="utf-8").strip()
                if txt:
                    default_url = txt
            except Exception:
                pass
        return {
            "enrolled": False,
            "server_url": default_url,
            "device_id": "",
            "enrollment_code": "",
            "agent_token": "",
            "device_secret": generate_device_secret(),
            "client_name": "",
            "client_cedula": "",
            "client_phone": "",
            "laptop_model": "Laptop Financiada",
            "laptop_serial": "",
            "hardware_id": hw_id,
            "hostname": hostname,
            "manual_status": "auto",
            "manual_unlock_until": None,
            "lock_reason_override": "",
            "installments": [],
            "used_pins": [],
            "last_sync_at": None,
            "last_warning_shown_date": None,
        }

    def _load(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return self._default_state()
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
            base = self._default_state()
            base.update(raw)
            return base
        except Exception:
            return self._default_state()

    def save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            json.dumps(self.state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @property
    def is_enrolled(self) -> bool:
        return bool(
            self.state.get("enrolled")
            and self.state.get("client_name")
            and self.state.get("client_cedula")
        )

    def evaluate_current_policy(self, today: date | None = None) -> dict[str, Any]:
        """Evalúa el estado actual de bloqueo y aviso de pago (1 día antes)."""
        return evaluate_device_policy(
            installments=self.state.get("installments", []),
            manual_status=self.state.get("manual_status", "auto"),
            manual_unlock_until=self.state.get("manual_unlock_until"),
            lock_reason_override=self.state.get("lock_reason_override", ""),
            today=today,
        )

    def enroll_with_server(
        self,
        server_url: str,
        enrollment_code: str = "",
        client_name: str = "",
        client_cedula: str = "",
        client_phone: str = "",
        laptop_model: str = "Laptop",
        laptop_serial: str = "",
        first_due_date: str = "",
        total_installments: int = 6,
        installment_amount: float = 85.0,
    ) -> dict[str, Any]:
        """Vincula esta laptop con el Servidor Central de Creditech."""
        clean_url = server_url.strip().rstrip("/")
        hw_id, hostname = get_hardware_fingerprint()
        payload = {
            "enrollment_code": enrollment_code.strip().upper(),
            "client_name": client_name.strip(),
            "client_cedula": client_cedula.strip(),
            "client_phone": client_phone.strip(),
            "laptop_model": laptop_model.strip() or "Laptop",
            "laptop_serial": laptop_serial.strip(),
            "hardware_id": hw_id,
            "hostname": hostname,
            "first_due_date": first_due_date,
            "total_installments": total_installments,
            "installment_amount": installment_amount,
        }

        with httpx.Client(timeout=8.0) as client:
            resp = client.post(f"{clean_url}/api/v1/agent/enroll", json=payload)
            if resp.status_code >= 400:
                try:
                    detail = resp.json().get("detail", resp.text)
                except Exception:
                    detail = resp.text
                raise RuntimeError(f"Error del servidor ({resp.status_code}): {detail}")
            data = resp.json()

        self._apply_server_payload(data, server_url=clean_url, include_secrets=True)
        return self.state

    def enroll_standalone_local(
        self,
        client_name: str,
        client_cedula: str,
        client_phone: str = "",
        laptop_model: str = "Laptop",
        laptop_serial: str = "",
        first_due_date: str = "",
        total_installments: int = 6,
        installment_amount: float = 85.0,
        frequency_days: int = 30,
        server_url: str = "",
    ) -> dict[str, Any]:
        """Registra la laptop localmente (modo autónomo sin servidor o cuando el servidor no responde).

        Deriva `device_secret` a partir de la cédula del cliente (`generate_device_secret(cedula)`)
        para que el vendedor pueda generar el PIN de desbloqueo desde la App de su teléfono
        desde cualquier lugar (con datos móviles o incluso sin internet) usando la misma cédula.
        """
        clean_cedula = client_cedula.strip()
        first_due = parse_iso_date(first_due_date) or (date.today() + timedelta(days=30))
        schedule = generate_installment_schedule(
            first_due_date=first_due,
            total_installments=total_installments,
            installment_amount=installment_amount,
            frequency_days=frequency_days,
        )
        self.state.update(
            {
                "enrolled": True,
                "server_url": server_url.strip().rstrip("/"),
                "enrollment_code": generate_enrollment_code(),
                "device_secret": generate_device_secret(cedula=clean_cedula),
                "client_name": client_name.strip(),
                "client_cedula": clean_cedula,
                "client_phone": client_phone.strip(),
                "laptop_model": laptop_model.strip() or "Laptop",
                "laptop_serial": laptop_serial.strip(),
                "manual_status": "auto",
                "manual_unlock_until": None,
                "lock_reason_override": "",
                "installments": schedule,
                "last_sync_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        self.save()
        return self.state

    def sync_with_server(self) -> tuple[bool, str]:
        """Envía heartbeat al servidor y descarga el estado más reciente de bloqueo y cuotas."""
        if not self.is_enrolled:
            return False, "Equipo aún no vinculado."
        server_url = (self.state.get("server_url") or "").strip().rstrip("/")
        device_id = self.state.get("device_id") or ""
        agent_token = self.state.get("agent_token") or ""
        if not server_url or not device_id or not agent_token:
            return False, "Sin credenciales de servidor configuradas (modo local)."

        policy = self.evaluate_current_policy()
        hw_id, hostname = get_hardware_fingerprint()

        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(
                    f"{server_url}/api/v1/agent/heartbeat",
                    headers={
                        "X-Device-Id": device_id,
                        "X-Agent-Token": agent_token,
                    },
                    json={
                        "hardware_id": hw_id,
                        "hostname": hostname,
                        "is_locked": bool(policy["locked"]),
                    },
                )
                if resp.status_code >= 400:
                    return False, f"Servidor respondió HTTP {resp.status_code}"
                data = resp.json()
                self._apply_server_payload(data, server_url=server_url, include_secrets=False)
                return True, "Sincronizado con el servidor Creditech."
        except Exception as exc:
            return False, f"Sin conexión con el servidor ({exc}). Operando con respaldo local."

    def _apply_server_payload(
        self,
        data: dict[str, Any],
        server_url: str,
        include_secrets: bool = False,
    ) -> None:
        self.state["enrolled"] = True
        self.state["server_url"] = server_url
        self.state["device_id"] = data.get("id", self.state.get("device_id", ""))
        self.state["enrollment_code"] = data.get(
            "enrollment_code", self.state.get("enrollment_code", "")
        )
        self.state["client_name"] = data.get("client_name", self.state.get("client_name", ""))
        self.state["client_cedula"] = data.get(
            "client_cedula", self.state.get("client_cedula", "")
        )
        self.state["client_phone"] = data.get("client_phone", self.state.get("client_phone", ""))
        self.state["laptop_model"] = data.get("laptop_model", self.state.get("laptop_model", ""))
        self.state["laptop_serial"] = data.get(
            "laptop_serial", self.state.get("laptop_serial", "")
        )
        self.state["manual_status"] = data.get("manual_status", "auto")
        self.state["manual_unlock_until"] = data.get("manual_unlock_until")
        self.state["lock_reason_override"] = data.get("lock_reason_override", "")
        self.state["installments"] = data.get("installments", [])
        self.state["last_sync_at"] = datetime.now().isoformat(timespec="seconds")

        if include_secrets:
            if data.get("device_secret"):
                self.state["device_secret"] = data["device_secret"]
            if data.get("agent_token"):
                self.state["agent_token"] = data["agent_token"]

        self.save()

    def apply_offline_pin(self, pin_code: str, reference_date: date | None = None) -> dict[str, Any]:
        """Verifica un PIN offline ingresado por el cliente y desbloquea la laptop si es válido."""
        res = verify_offline_pin(
            pin=pin_code,
            device_secret=self.state.get("device_secret", ""),
            cedula=self.state.get("client_cedula", ""),
            reference_date=reference_date,
            used_pins=self.state.get("used_pins", []),
        )
        if not res["valid"]:
            return res

        used = list(self.state.get("used_pins", []))
        used.append(res["normalized_pin"])
        self.state["used_pins"] = used

        ref = reference_date or date.today()
        if res["permanent"]:
            self.state["manual_status"] = "unlocked"
            self.state["manual_unlock_until"] = None
            self.state["lock_reason_override"] = ""
        else:
            grace_until = ref + timedelta(days=int(res["unlock_days"]))
            self.state["manual_unlock_until"] = grace_until.isoformat()
            if self.state.get("manual_status") == "locked":
                self.state["manual_status"] = "auto"
                self.state["lock_reason_override"] = ""

            # Si el PIN corresponde a la próxima cuota vencida/pendiente, marcarla pagada localmente
            inst_list = self.state.get("installments", [])
            pending = [i for i in inst_list if i.get("status") != "paid"]
            if pending:
                pending.sort(key=lambda x: int(x.get("number", 1)))
                pending[0]["status"] = "paid"
                pending[0]["paid_at"] = ref.isoformat()

        self.save()
        return res
