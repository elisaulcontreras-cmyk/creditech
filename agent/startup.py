"""Persistencia en Windows para el Agente Creditech.

Permite registrar el agente en el inicio automático de Windows
(`HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`) para que el programa
se inicie automáticamente apenas el cliente encienda la laptop.
"""

from __future__ import annotations

import sys
from pathlib import Path


def install_windows_startup(app_name: str = "CreditechAgent") -> tuple[bool, str]:
    """Registra el agente Creditech en el arranque de usuario de Windows.

    Si se está ejecutando desde el ejecutable empaquetado (`Creditech_Agente_Laptop.exe`),
    copia automáticamente el `.exe` a `%LOCALAPPDATA%\\Creditech\\Creditech_Agente_Laptop.exe`
    y registra esa ruta permanente en el inicio de Windows para que siga funcionando
    aunque se retire el pendrive USB de instalación.
    """
    if sys.platform != "win32":
        return False, "El inicio automático de registro solo aplica en Windows."
    try:
        import os
        import shutil
        import winreg

        if getattr(sys, "frozen", False):
            current_exe = Path(sys.executable).resolve()
            local_appdata = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
            install_dir = Path(local_appdata) / "Creditech"
            install_dir.mkdir(parents=True, exist_ok=True)
            target_exe = install_dir / "Creditech_Agente_Laptop.exe"
            if current_exe != target_exe:
                try:
                    shutil.copy2(current_exe, target_exe)
                except Exception:
                    target_exe = current_exe
            cmd = f'"{target_exe}"'
        else:
            repo_root = Path(__file__).resolve().parent.parent
            launcher_script = repo_root / "run_agent.py"
            python_exe = Path(sys.executable)
            pythonw_exe = python_exe.with_name("pythonw.exe")
            exe_to_use = pythonw_exe if pythonw_exe.exists() else python_exe
            cmd = f'"{exe_to_use}" "{launcher_script}"'

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, cmd)
        return True, f"Inicio automático configurado en Windows ({app_name})."
    except Exception as exc:
        return False, f"No se pudo registrar en el inicio de Windows: {exc}"
