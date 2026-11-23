"""Punto de entrada para ejecutar el Servidor Central de Creditech."""

from __future__ import annotations

import os
import uvicorn


def main() -> None:
    host = os.environ.get("CREDITECH_HOST", "0.0.0.0")
    port = int(os.environ.get("CREDITECH_PORT", "8085"))
    print(f"Iniciando Servidor Central Creditech en http://localhost:{port} ...")
    uvicorn.run("server.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
