"""Lanzador del Agente de Laptop Creditech (para instalar en los equipos de clientes)."""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from agent.state import AgentStateManager
from agent.ui import ClientPortalWindow, EnrollmentDialog


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Creditech")
    app.setOrganizationName("Creditech")

    state_mgr = AgentStateManager()

    if not state_mgr.is_enrolled:
        dlg = EnrollmentDialog(state_mgr)
        if dlg.exec() != EnrollmentDialog.DialogCode.Accepted:
            return 0

    window = ClientPortalWindow(state_mgr)
    window.show()
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(400, window.periodic_check)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
