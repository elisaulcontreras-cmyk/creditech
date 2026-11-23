"""Pruebas offscreen de la interfaz PyQt6 del Agente Creditech."""

from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from agent.state import AgentStateManager
from agent.ui import ClientPortalWindow, PaymentReminderDialog


def test_agent_ui_renders_client_name_and_cedula(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    state_path = tmp_path / "ui_state.json"
    mgr = AgentStateManager(state_path=state_path)

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    mgr.state.update(
        {
            "enrolled": True,
            "client_name": "Carlos Eduardo Pérez",
            "client_cedula": "V-18.452.910",
            "laptop_model": "Lenovo ThinkPad T14",
            "laptop_serial": "PF-998877",
            "enrollment_code": "CRD-1234-5678",
            "installments": [
                {"number": 1, "due_date": tomorrow, "amount": 85.0, "status": "pending"},
            ],
        }
    )
    mgr.save()

    win = ClientPortalWindow(mgr)
    win.refresh_ui()

    assert "Carlos Eduardo Pérez" in win.client_name_lbl.text()
    assert "V-18.452.910" in win.client_cedula_lbl.text()
    assert win.warning_frame.isHidden() is False
    assert "MAÑANA" in win.warning_label.text()

    # Probar pantalla de bloqueo con nombre y cédula
    mgr.state["manual_status"] = "locked"
    mgr.state["lock_reason_override"] = "Bloqueado desde servidor por cuota impaga."
    win.lock_window.refresh_lock_info()
    assert "Carlos Eduardo Pérez" in win.lock_window.client_name_lbl.text()
    assert "V-18.452.910" in win.lock_window.client_cedula_lbl.text()
    assert "Bloqueado desde servidor" in win.lock_window.reason_lbl.text()
