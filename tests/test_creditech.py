"""Suite de pruebas automatizadas para Creditech.

Verifica:
1. Aviso de pago exactamente 1 día antes del vencimiento (`days_until_due == 1`).
2. Bloqueo automático del equipo cuando el cliente no paga una cuota vencida.
3. Bloqueo y desbloqueo remoto desde el Servidor Central.
4. Registro de múltiples equipos con Nombre y Número de Cédula del cliente.
5. Generación y verificación de PINs de desbloqueo offline (sin internet) y protección
   contra reutilización del mismo PIN.
6. Sincronización (enroll + heartbeat) entre el Agente de Laptop y el Servidor.
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agent.state import AgentStateManager
from server.app import app
from server.models import init_server_db
from shared.crypto import generate_device_secret, generate_offline_pin, verify_offline_pin
from shared.policy import evaluate_device_policy


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "test_creditech.db"
    db_url = f"sqlite:///{db_file}"
    monkeypatch.setenv("CREDITECH_SERVER_DB", db_url)
    init_server_db(db_url)
    yield


def test_reminder_one_day_before_due_date():
    """El sistema debe activar el aviso de pago 1 día antes del vencimiento sin bloquear."""
    today = date(2026, 11, 23)
    due_tomorrow = (today + timedelta(days=1)).isoformat()

    installments = [
        {"number": 1, "due_date": due_tomorrow, "amount": 95.0, "status": "pending"},
    ]
    policy = evaluate_device_policy(installments=installments, today=today)

    assert policy["locked"] is False
    assert policy["warning_due_soon"] is True
    assert policy["days_until_due"] == 1
    assert "MAÑANA" in policy["warning_message"]
    assert "$95.00" in policy["warning_message"]


def test_auto_lock_when_installment_is_overdue():
    """El sistema debe bloquear automáticamente el equipo cuando la cuota ya venció y no se pagó."""
    today = date(2026, 11, 23)
    due_yesterday = (today - timedelta(days=1)).isoformat()

    installments = [
        {"number": 1, "due_date": due_yesterday, "amount": 95.0, "status": "pending"},
    ]
    policy = evaluate_device_policy(installments=installments, today=today)

    assert policy["locked"] is True
    assert "Cuota #1 vencida" in policy["lock_reason"]
    assert len(policy["overdue_installments"]) == 1


def test_offline_pin_generation_and_verification():
    """El PIN offline debe validar con el secreto del equipo y la cédula del cliente, e impedir reúso."""
    secret = generate_device_secret()
    cedula = "V-18.452.910"
    ref_date = date(2026, 11, 23)

    pin = generate_offline_pin(
        device_secret=secret,
        cedula=cedula,
        unlock_days=30,
        reference_date=ref_date,
    )

    # Debe ser válido con la misma cédula (incluso escrita sin puntos ni guiones)
    res_ok = verify_offline_pin(
        pin=pin,
        device_secret=secret,
        cedula="v18452910",
        reference_date=ref_date,
    )
    assert res_ok["valid"] is True
    assert res_ok["unlock_days"] == 30

    # No debe funcionar con otra cédula
    res_wrong_cedula = verify_offline_pin(
        pin=pin,
        device_secret=secret,
        cedula="V-99.999.999",
        reference_date=ref_date,
    )
    assert res_wrong_cedula["valid"] is False

    # No debe permitir reutilizar un PIN ya consumido
    res_replay = verify_offline_pin(
        pin=pin,
        device_secret=secret,
        cedula=cedula,
        reference_date=ref_date,
        used_pins=[pin],
    )
    assert res_replay["valid"] is False


def test_server_multi_device_and_remote_lock_unlock(tmp_path: Path):
    """El servidor debe permitir registrar varias laptops con nombre y cédula, y bloquearlas/desbloquearlas."""
    client = TestClient(app)
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Registrar Laptop 1
    r1 = client.post(
        "/api/v1/devices",
        json={
            "client_name": "María Fernanda Rojas",
            "client_cedula": "V-20.111.222",
            "client_phone": "+58 412-1112233",
            "laptop_model": "Lenovo IdeaPad 3",
            "laptop_serial": "SN-LEN-001",
            "first_due_date": tomorrow,
            "total_installments": 6,
            "installment_amount": 80.0,
            "frequency_days": 30,
        },
    )
    assert r1.status_code == 200
    dev1 = r1.json()
    assert dev1["client_name"] == "María Fernanda Rojas"
    assert dev1["client_cedula"] == "V-20.111.222"
    assert dev1["policy"]["locked"] is False
    assert dev1["policy"]["warning_due_soon"] is True  # Vence mañana (1 día antes)

    # Registrar Laptop 2
    r2 = client.post(
        "/api/v1/devices",
        json={
            "client_name": "José Gregorio Silva",
            "client_cedula": "V-15.999.888",
            "laptop_model": "HP Pavilion 15",
            "laptop_serial": "SN-HP-002",
            "first_due_date": tomorrow,
            "total_installments": 4,
            "installment_amount": 110.0,
            "frequency_days": 15,
        },
    )
    assert r2.status_code == 200
    dev2 = r2.json()
    assert dev1["enrollment_code"] != dev2["enrollment_code"]

    # Vincular Agente de Laptop 1 usando su código de instalación
    enroll_res = client.post(
        "/api/v1/agent/enroll",
        json={
            "enrollment_code": dev1["enrollment_code"],
            "hardware_id": "HW-TEST-001",
            "hostname": "LAPTOP-MARIA",
        },
    )
    assert enroll_res.status_code == 200
    enrolled_data = enroll_res.json()
    token = enrolled_data["agent_token"]

    # Bloquear Laptop 1 remotamente desde el servidor
    lock_res = client.post(
        f"/api/v1/devices/{dev1['id']}/lock",
        json={"reason": "Bloqueo administrativo por falta de pago de cuota."},
    )
    assert lock_res.status_code == 200
    assert lock_res.json()["policy"]["locked"] is True

    # Heartbeat desde la laptop debe recibir orden de bloqueo
    hb_locked = client.post(
        "/api/v1/agent/heartbeat",
        headers={"X-Device-Id": dev1["id"], "X-Agent-Token": token},
        json={"hardware_id": "HW-TEST-001", "hostname": "LAPTOP-MARIA", "is_locked": True},
    )
    assert hb_locked.status_code == 200
    assert hb_locked.json()["policy"]["locked"] is True
    assert "Bloqueo administrativo" in hb_locked.json()["policy"]["lock_reason"]

    # Desbloquear Laptop 1 remotamente desde el servidor
    unlock_res = client.post(
        f"/api/v1/devices/{dev1['id']}/unlock",
        json={"mode": "auto", "grace_days": 3},
    )
    assert unlock_res.status_code == 200
    assert unlock_res.json()["policy"]["locked"] is False

    # Generar PIN offline desde el servidor y probarlo en un AgentStateManager local
    pin_res = client.post(
        f"/api/v1/devices/{dev1['id']}/offline-pin",
        json={"unlock_days": 30},
    )
    assert pin_res.status_code == 200
    pin_code = pin_res.json()["pin"]

    # Marcar la primera cuota de María como pagada y verificar montos pagado / pendiente
    first_inst_id = dev1["installments"][0]["id"]
    pay_res = client.post(f"/api/v1/devices/{dev1['id']}/installments/{first_inst_id}/pay")
    assert pay_res.status_code == 200
    paid_dev = pay_res.json()
    assert paid_dev["paid_amount"] == 80.0
    assert paid_dev["pending_amount"] == 400.0  # 5 cuotas restantes de $80

    # Descargar reporte Excel (.xlsx) de personas que deben dinero
    excel_res = client.get("/api/v1/reports/debtors.xlsx")
    assert excel_res.status_code == 200
    assert (
        excel_res.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    # Un archivo .xlsx es un contenedor ZIP que empieza con bytes PK\x03\x04
    assert excel_res.content[:4] == b"PK\x03\x04"

    # Verificar endpoints PWA para instalar como App en el teléfono celular
    manifest_res = client.get("/manifest.json")
    assert manifest_res.status_code == 200
    assert manifest_res.json()["short_name"] == "Creditech"

    icon_res = client.get("/icon.svg")
    assert icon_res.status_code == 200
    assert "indatech." in icon_res.text

    sw_res = client.get("/sw.js")
    assert sw_res.status_code == 200

    state_file = tmp_path / "agent_state.json"
    mgr = AgentStateManager(state_path=state_file)
    mgr._apply_server_payload(enrolled_data, server_url="http://testserver", include_secrets=True)
    # Simular que está bloqueado localmente
    mgr.state["manual_status"] = "locked"
    mgr.save()
    assert mgr.evaluate_current_policy()["locked"] is True

    # Desbloquear con el PIN offline
    verify_res = mgr.apply_offline_pin(pin_code)
    assert verify_res["valid"] is True
    assert mgr.evaluate_current_policy()["locked"] is False
