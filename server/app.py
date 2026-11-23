"""Servidor Central FastAPI para Creditech.

Expone:
1. Panel Web de Administración (`GET /`) para gestionar clientes (nombre y cédula),
   laptops financiadas, cronogramas de cuotas, bloqueos/desbloqueos remotos y PINs offline.
2. API de Administración (`/api/v1/devices/...`):
   - Crear cliente/laptop con generación automática de cuotas.
   - Listar equipos con su estado evaluado en tiempo real (al día, aviso 1 día antes, bloqueado).
   - Bloquear equipo remotamente (`POST /api/v1/devices/{id}/lock`).
   - Desbloquear equipo remotamente (`POST /api/v1/devices/{id}/unlock`).
   - Registrar pago de cuota (`POST /api/v1/devices/{id}/installments/{inst_id}/pay`).
   - Generar PIN de desbloqueo offline (`POST /api/v1/devices/{id}/offline-pin`).
3. API para el Agente instalado en las Laptops (`/api/v1/agent/...`):
   - `POST /api/v1/agent/enroll`: Vincula una laptop usando el código de instalación
     (`CRD-XXXX-XXXX`), o registra directamente nombre y cédula desde el instalador.
   - `POST /api/v1/agent/heartbeat`: La laptop reporta que está encendida y recibe
     su estado actualizado (si debe bloquearse, si debe mostrar el aviso 1 día antes
     del vencimiento, y la lista actualizada de cuotas).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import os
import secrets
from datetime import date, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field
from sqlalchemy import select

from server.dashboard import DASHBOARD_HTML
from server.excel_report import build_excel_report_bytes, save_automatic_excel_backup
from shared.branding import INDATECH_ICON_SVG, INDATECH_LOGO_SVG
from server.models import (
    Device,
    DeviceEvent,
    Installment,
    generate_installment_schedule,
    get_session,
    init_server_db,
    utcnow,
)
from shared.crypto import generate_device_secret, generate_offline_pin
from shared.policy import evaluate_device_policy, parse_iso_date


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    init_server_db()
    yield


app = FastAPI(
    title="Creditech Server",
    description="Servidor Central de Control y Financiamiento de Laptops Creditech",
    version="1.0.0",
    lifespan=_lifespan,
)

_security = HTTPBasic(auto_error=False)


def verify_admin(credentials: Optional[HTTPBasicCredentials] = Depends(_security)) -> None:
    """Protege el Panel Web y rutas de administración si se configura CREDITECH_ADMIN_PASSWORD en el VPS."""
    expected_pass = os.environ.get("CREDITECH_ADMIN_PASSWORD", "").strip()
    if not expected_pass:
        # Si no se configuró contraseña en el entorno local, permite acceso directo
        return
    expected_user = os.environ.get("CREDITECH_ADMIN_USER", "admin").strip() or "admin"
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso restringido a administradores de Creditech by indatech.",
            headers={"WWW-Authenticate": 'Basic realm="Creditech Admin"'},
        )
    user_ok = secrets.compare_digest(credentials.username, expected_user)
    pass_ok = secrets.compare_digest(credentials.password, expected_pass)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña de administrador incorrectos.",
            headers={"WWW-Authenticate": 'Basic realm="Creditech Admin"'},
        )


# ---------------------------------------------------------------------------
# Esquemas Pydantic
# ---------------------------------------------------------------------------


class CreateDeviceRequest(BaseModel):
    client_name: str = Field(..., min_length=2, description="Nombre completo del cliente")
    client_cedula: str = Field(..., min_length=3, description="Número de cédula del cliente")
    client_phone: str = ""
    client_address: str = ""
    laptop_model: str = "Laptop"
    laptop_serial: str = ""
    first_due_date: str = Field(..., description="Fecha de vencimiento de la 1ª cuota (YYYY-MM-DD)")
    total_installments: int = Field(default=6, ge=1, le=60)
    installment_amount: float = Field(default=80.0, ge=0.0)
    frequency_days: int = Field(default=30, ge=1, le=365)


class LockDeviceRequest(BaseModel):
    reason: str = "Equipo bloqueado por mora en el pago de cuotas. Comuníquese con Creditech."


class UnlockDeviceRequest(BaseModel):
    mode: str = "auto"  # 'auto' o 'unlocked' (permanente)
    grace_days: int = Field(default=3, ge=0, le=90)


class OfflinePinRequest(BaseModel):
    unlock_days: int = Field(default=30, ge=1, le=99)
    installment_number: int = Field(default=0, ge=0, le=60)


class AgentEnrollRequest(BaseModel):
    enrollment_code: str = ""
    client_name: str = ""
    client_cedula: str = ""
    client_phone: str = ""
    laptop_model: str = "Laptop"
    laptop_serial: str = ""
    hardware_id: str = ""
    hostname: str = ""
    first_due_date: str = ""
    total_installments: int = 6
    installment_amount: float = 85.0


class AgentHeartbeatRequest(BaseModel):
    hardware_id: str = ""
    hostname: str = ""
    is_locked: bool = False


# ---------------------------------------------------------------------------
# Helpers de serialización
# ---------------------------------------------------------------------------


def serialize_device(dev: Device, include_secret: bool = False, today: date | None = None) -> dict:
    """Convierte un objeto `Device` y sus cuotas en un diccionario con su política evaluada."""
    inst_list = [
        {
            "id": i.id,
            "number": i.number,
            "due_date": i.due_date,
            "amount": i.amount,
            "status": i.status,
            "paid_at": i.paid_at,
            "notes": i.notes,
        }
        for i in sorted(dev.installments, key=lambda x: x.number)
    ]
    total_amount = round(sum(float(i["amount"]) for i in inst_list), 2)
    paid_amount = round(
        sum(float(i["amount"]) for i in inst_list if i["status"] == "paid"), 2
    )
    pending_amount = round(total_amount - paid_amount, 2)

    policy = evaluate_device_policy(
        installments=inst_list,
        manual_status=dev.manual_status,
        manual_unlock_until=dev.manual_unlock_until,
        lock_reason_override=dev.lock_reason_override,
        today=today,
    )
    payload = {
        "id": dev.id,
        "client_name": dev.client_name,
        "client_cedula": dev.client_cedula,
        "client_phone": dev.client_phone,
        "client_address": dev.client_address,
        "laptop_model": dev.laptop_model,
        "laptop_serial": dev.laptop_serial,
        "hardware_id": dev.hardware_id,
        "hostname": dev.hostname,
        "enrollment_code": dev.enrollment_code,
        "manual_status": dev.manual_status,
        "manual_unlock_until": dev.manual_unlock_until,
        "lock_reason_override": dev.lock_reason_override,
        "last_seen_at": dev.last_seen_at.isoformat() if dev.last_seen_at else None,
        "last_reported_locked": bool(dev.last_reported_locked),
        "last_ip": dev.last_ip,
        "total_amount": total_amount,
        "paid_amount": paid_amount,
        "pending_amount": pending_amount,
        "installments": inst_list,
        "policy": policy,
    }
    if include_secret:
        payload["device_secret"] = dev.device_secret
        payload["agent_token"] = dev.agent_token
    return payload


# ---------------------------------------------------------------------------
# Rutas del Panel Web y Administración
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse, dependencies=[Depends(verify_admin)])
def web_dashboard() -> HTMLResponse:
    """Sirve el Panel Central de Administración de Creditech (optimizado para Celular PWA y PC)."""
    return HTMLResponse(content=DASHBOARD_HTML)


@app.get("/manifest.json")
def pwa_manifest() -> JSONResponse:
    """Manifiesto PWA para instalar Creditech by indatech. como App nativa en Android y iPhone."""
    return JSONResponse(
        content={
            "name": "Creditech by indatech.",
            "short_name": "Creditech",
            "description": "Control de Laptops Financiadas, Bloqueo Remoto, PINs y Excel de Deudores",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#071D20",
            "theme_color": "#071D20",
            "orientation": "portrait-primary",
            "icons": [
                {
                    "src": "/icon.svg",
                    "sizes": "any",
                    "type": "image/svg+xml",
                    "purpose": "any maskable",
                }
            ],
        }
    )


@app.get("/icon.svg")
def pwa_icon_svg() -> Response:
    """Icono vectorial oficial de indatech. para la pantalla de inicio del teléfono."""
    return Response(content=INDATECH_LOGO_SVG, media_type="image/svg+xml")


@app.get("/sw.js")
def pwa_service_worker() -> Response:
    """Service Worker ligero para habilitar la instalación PWA en Android/iOS."""
    js = """
    const CACHE_NAME = 'creditech-pwa-v2';
    self.addEventListener('install', (e) => {
      e.waitUntil(
        caches.open(CACHE_NAME).then((c) => c.addAll(['/', '/manifest.json', '/icon.svg']))
      );
      self.skipWaiting();
    });
    self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
    self.addEventListener('fetch', (e) => {
      if (e.request.method !== 'GET') return;
      e.respondWith(
        fetch(e.request)
          .then((res) => {
            const copy = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(e.request, copy));
            return res;
          })
          .catch(() => caches.match(e.request))
      );
    });
    """
    return Response(content=js.strip(), media_type="application/javascript")


@app.get("/api/v1/health")
def health_check() -> dict:
    return {"status": "ok", "app": "Creditech Server", "version": "1.0.0"}


@app.get("/api/v1/devices", dependencies=[Depends(verify_admin)])
def list_devices() -> dict:
    with get_session() as s:
        devices = s.scalars(select(Device).order_by(Device.created_at.desc())).all()
        return {"devices": [serialize_device(d) for d in devices]}


@app.get("/api/v1/reports/debtors.xlsx", dependencies=[Depends(verify_admin)])
def export_debtors_excel() -> Response:
    """Genera y descarga el archivo Excel (.xlsx) de respaldo con deudores, lo pagado y lo que falta."""
    with get_session() as s:
        devices = s.scalars(select(Device).order_by(Device.created_at.desc())).all()
        xlsx_bytes = build_excel_report_bytes(devices)
        try:
            save_automatic_excel_backup(devices)
        except Exception:
            pass
    filename = f"respaldo_deudores_creditech_{date.today().isoformat()}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


class GitHubPagesExportRequest(BaseModel):
    devices: list[dict] = []


@app.post("/api/v1/reports/debtors-from-json.xlsx")
def export_debtors_excel_from_json(req: GitHubPagesExportRequest) -> Response:
    """Genera el Excel (.xlsx) a partir de la lista de equipos enviada por la App PWA de GitHub Pages."""
    dummy_devices = []
    for idx, d in enumerate(req.devices):
        dev = Device(
            id=str(d.get("id") or f"dev_{idx}"),
            client_name=str(d.get("client_name") or "Cliente"),
            client_cedula=str(d.get("client_cedula") or "N/A"),
            client_phone=str(d.get("client_phone") or ""),
            laptop_model=str(d.get("laptop_model") or "Laptop"),
            laptop_serial=str(d.get("laptop_serial") or ""),
            enrollment_code=str(d.get("enrollment_code") or "CRD-0000"),
            manual_status=str(d.get("manual_status") or "auto"),
            manual_unlock_until=d.get("manual_unlock_until"),
            lock_reason_override=str(d.get("lock_reason_override") or ""),
        )
        dev.installments = [
            Installment(
                id=str(inst.get("id") or f"inst_{idx}_{n}"),
                device_id=dev.id,
                number=int(inst.get("number", n + 1)),
                due_date=str(inst.get("due_date") or date.today().isoformat()),
                amount=float(inst.get("amount", 0.0)),
                status=str(inst.get("status") or "pending"),
                paid_at=inst.get("paid_at"),
            )
            for n, inst in enumerate(d.get("installments") or [])
        ]
        dummy_devices.append(dev)
    xlsx_bytes = build_excel_report_bytes(dummy_devices)
    filename = f"respaldo_deudores_creditech_{date.today().isoformat()}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
    first_due = parse_iso_date(req.first_due_date)
    if first_due is None:
        raise HTTPException(status_code=400, detail="Fecha de 1ª cuota inválida (use YYYY-MM-DD).")

    with get_session() as s:
        clean_cedula = req.client_cedula.strip()
        dev = Device(
            client_name=req.client_name.strip(),
            client_cedula=clean_cedula,
            client_phone=req.client_phone.strip(),
            client_address=req.client_address.strip(),
            laptop_model=req.laptop_model.strip() or "Laptop",
            laptop_serial=req.laptop_serial.strip(),
            device_secret=generate_device_secret(cedula=clean_cedula),
            agent_token=secrets.token_hex(24),
        )
        s.add(dev)
        s.flush()

        schedule = generate_installment_schedule(
            first_due_date=first_due,
            total_installments=req.total_installments,
            installment_amount=req.installment_amount,
            frequency_days=req.frequency_days,
        )
        for item in schedule:
            s.add(
                Installment(
                    device_id=dev.id,
                    number=item["number"],
                    due_date=item["due_date"],
                    amount=item["amount"],
                    status=item["status"],
                )
            )

        s.add(
            DeviceEvent(
                device_id=dev.id,
                event_type="created",
                description=(
                    f"Cliente {dev.client_name} ({dev.client_cedula}) registrado con "
                    f"{req.total_installments} cuotas de ${req.installment_amount:.2f}."
                ),
            )
        )
        s.commit()
        s.refresh(dev)
        try:
            all_devs = s.scalars(select(Device).order_by(Device.created_at.desc())).all()
            save_automatic_excel_backup(all_devs)
        except Exception:
            pass
        return serialize_device(dev, include_secret=True)


@app.get("/api/v1/devices/{device_id}", dependencies=[Depends(verify_admin)])
def get_device(device_id: str) -> dict:
    with get_session() as s:
        dev = s.get(Device, device_id)
        if not dev:
            raise HTTPException(status_code=404, detail="Equipo no encontrado.")
        return serialize_device(dev)


@app.post("/api/v1/devices/{device_id}/lock", dependencies=[Depends(verify_admin)])
def lock_device(device_id: str, req: LockDeviceRequest) -> dict:
    """Bloquea remotamente una laptop desde el servidor."""
    with get_session() as s:
        dev = s.get(Device, device_id)
        if not dev:
            raise HTTPException(status_code=404, detail="Equipo no encontrado.")
        dev.manual_status = "locked"
        dev.manual_unlock_until = None
        dev.lock_reason_override = (
            req.reason.strip()
            or "Equipo bloqueado remotamente por falta de pago. Comuníquese con Creditech."
        )
        s.add(
            DeviceEvent(
                device_id=dev.id,
                event_type="remote_lock",
                description=f"Bloqueo remoto activado: {dev.lock_reason_override}",
            )
        )
        s.commit()
        s.refresh(dev)
        return serialize_device(dev)


@app.post("/api/v1/devices/{device_id}/unlock", dependencies=[Depends(verify_admin)])
def unlock_device(device_id: str, req: UnlockDeviceRequest) -> dict:
    """Desbloquea remotamente una laptop desde el servidor."""
    with get_session() as s:
        dev = s.get(Device, device_id)
        if not dev:
            raise HTTPException(status_code=404, detail="Equipo no encontrado.")
        mode = req.mode if req.mode in ("auto", "unlocked") else "auto"
        dev.manual_status = mode
        dev.lock_reason_override = ""
        if req.grace_days > 0:
            grace_until = date.today() + timedelta(days=req.grace_days)
            dev.manual_unlock_until = grace_until.isoformat()
        else:
            dev.manual_unlock_until = None

        s.add(
            DeviceEvent(
                device_id=dev.id,
                event_type="remote_unlock",
                description=(
                    f"Desbloqueo remoto ejecutado (modo={mode}, "
                    f"gracia hasta={dev.manual_unlock_until or 'ninguna'})."
                ),
            )
        )
        s.commit()
        s.refresh(dev)
        return serialize_device(dev)


@app.post("/api/v1/devices/{device_id}/installments/{installment_id}/pay", dependencies=[Depends(verify_admin)])
def pay_installment(device_id: str, installment_id: str) -> dict:
    """Marca una cuota como pagada y restablece el bloqueo si no quedan cuotas en mora."""
    with get_session() as s:
        dev = s.get(Device, device_id)
        if not dev:
            raise HTTPException(status_code=404, detail="Equipo no encontrado.")
        inst = s.get(Installment, installment_id)
        if not inst or inst.device_id != dev.id:
            raise HTTPException(status_code=404, detail="Cuota no encontrada.")

        inst.status = "paid"
        inst.paid_at = utcnow().isoformat()

        # Si el equipo estaba bloqueado manualmente por mora, volver a modo automático
        if dev.manual_status == "locked":
            dev.manual_status = "auto"
            dev.lock_reason_override = ""

        s.add(
            DeviceEvent(
                device_id=dev.id,
                event_type="payment",
                description=f"Cuota #{inst.number} (${inst.amount:.2f}) marcada como PAGADA.",
            )
        )
        s.commit()
        s.refresh(dev)
        try:
            all_devs = s.scalars(select(Device).order_by(Device.created_at.desc())).all()
            save_automatic_excel_backup(all_devs)
        except Exception:
            pass
        return serialize_device(dev)


@app.post("/api/v1/devices/{device_id}/offline-pin", dependencies=[Depends(verify_admin)])
def create_offline_pin(device_id: str, req: OfflinePinRequest) -> dict:
    """Genera un PIN firmado con HMAC-SHA256 para desbloquear la laptop sin internet."""
    with get_session() as s:
        dev = s.get(Device, device_id)
        if not dev:
            raise HTTPException(status_code=404, detail="Equipo no encontrado.")

        pin = generate_offline_pin(
            device_secret=dev.device_secret,
            cedula=dev.client_cedula,
            unlock_days=req.unlock_days,
            installment_number=req.installment_number,
        )
        s.add(
            DeviceEvent(
                device_id=dev.id,
                event_type="offline_pin",
                description=f"PIN offline emitido por {req.unlock_days} días: {pin}",
            )
        )
        s.commit()
        return {
            "device_id": dev.id,
            "client_name": dev.client_name,
            "client_cedula": dev.client_cedula,
            "unlock_days": req.unlock_days,
            "pin": pin,
        }


# ---------------------------------------------------------------------------
# Rutas para el Agente instalado en cada Laptop
# ---------------------------------------------------------------------------


@app.post("/api/v1/agent/enroll")
def agent_enroll(req: AgentEnrollRequest, request: Request) -> dict:
    """Vincula una laptop al servidor Creditech.

    Puede vincularse de dos formas:
    1. Con `enrollment_code` (`CRD-XXXX-XXXX`) generado previamente en el panel web.
    2. Directamente ingresando `client_name` y `client_cedula` durante la instalación
       en la laptop (crea el registro en el servidor automáticamente).
    """
    with get_session() as s:
        dev: Optional[Device] = None
        code = (req.enrollment_code or "").strip().upper()
        if code:
            dev = s.scalar(select(Device).where(Device.enrollment_code == code))
            if not dev:
                raise HTTPException(
                    status_code=404,
                    detail=f"No existe ningún equipo con el código de instalación {code}.",
                )
        else:
            if not req.client_name.strip() or not req.client_cedula.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Debe indicar el Código de Instalación o el Nombre y Número de Cédula del cliente.",
                )
            first_due = parse_iso_date(req.first_due_date) or (date.today() + timedelta(days=30))
            clean_cedula = req.client_cedula.strip()
            dev = Device(
                client_name=req.client_name.strip(),
                client_cedula=clean_cedula,
                client_phone=req.client_phone.strip(),
                laptop_model=req.laptop_model.strip() or "Laptop",
                laptop_serial=req.laptop_serial.strip(),
                device_secret=generate_device_secret(cedula=clean_cedula),
                agent_token=secrets.token_hex(24),
            )
            s.add(dev)
            s.flush()
            schedule = generate_installment_schedule(
                first_due_date=first_due,
                total_installments=req.total_installments,
                installment_amount=req.installment_amount,
            )
            for item in schedule:
                s.add(
                    Installment(
                        device_id=dev.id,
                        number=item["number"],
                        due_date=item["due_date"],
                        amount=item["amount"],
                        status=item["status"],
                    )
                )

        if not dev.agent_token:
            dev.agent_token = secrets.token_hex(24)
        if req.hardware_id:
            dev.hardware_id = req.hardware_id.strip()
        if req.hostname:
            dev.hostname = req.hostname.strip()
        if req.laptop_model and dev.laptop_model == "Laptop":
            dev.laptop_model = req.laptop_model.strip()
        if req.laptop_serial and not dev.laptop_serial:
            dev.laptop_serial = req.laptop_serial.strip()

        dev.last_seen_at = utcnow()
        dev.last_ip = request.client.host if request.client else ""

        s.add(
            DeviceEvent(
                device_id=dev.id,
                event_type="enrolled",
                description=(
                    f"Laptop vinculada (hostname={dev.hostname or 'N/A'}, "
                    f"hw={dev.hardware_id or 'N/A'})."
                ),
            )
        )
        s.commit()
        s.refresh(dev)
        try:
            all_devs = s.scalars(select(Device).order_by(Device.created_at.desc())).all()
            save_automatic_excel_backup(all_devs)
        except Exception:
            pass
        return serialize_device(dev, include_secret=True)


@app.post("/api/v1/agent/heartbeat")
def agent_heartbeat(
    req: AgentHeartbeatRequest,
    request: Request,
    x_device_id: Optional[str] = Header(default=None),
    x_agent_token: Optional[str] = Header(default=None),
) -> dict:
    """Sincronización periódica desde la laptop hacia el servidor.

    Devuelve la información del cliente (nombre y cédula), el cronograma de cuotas
    actualizado, si corresponde mostrar el aviso de pago 1 día antes y si el equipo
    debe bloquearse o desbloquearse.
    """
    if not x_device_id or not x_agent_token:
        raise HTTPException(status_code=401, detail="Faltan credenciales del agente (X-Device-Id / X-Agent-Token).")

    with get_session() as s:
        dev = s.get(Device, x_device_id)
        if not dev or not secrets.compare_digest(dev.agent_token or "", x_agent_token):
            raise HTTPException(status_code=401, detail="Token de agente inválido.")

        dev.last_seen_at = utcnow()
        dev.last_reported_locked = 1 if req.is_locked else 0
        if req.hardware_id:
            dev.hardware_id = req.hardware_id
        if req.hostname:
            dev.hostname = req.hostname
        if request.client:
            dev.last_ip = request.client.host

        s.commit()
        s.refresh(dev)
        return serialize_device(dev, include_secret=False)
