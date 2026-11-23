"""Modelos de base de datos SQLAlchemy 2.0 para el servidor Creditech.

Almacena:
- `Device`: Cada laptop vendida a crédito, con los datos del cliente
  (nombre completo, número de cédula, teléfono), identificación del equipo
  (marca/modelo, serial, código de instalación, secreto HMAC, token de agente),
  estado de control remoto (`auto`, `locked`, `unlocked`), periodo de gracia
  y último contacto (`last_seen_at`).
- `Installment`: Cada cuota del plan de financiamiento del equipo (número de cuota,
  fecha de vencimiento, monto, estado `pending` o `paid`, fecha de pago).
- `DeviceEvent`: Bitácora de auditoría (registro, pagos, bloqueos remotos,
  desbloqueos, PINs emitidos y sincronizaciones del agente).
"""

from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

from shared.crypto import generate_device_secret, generate_enrollment_code


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class Device(Base):
    """Laptop financiada y asignada a un cliente en Creditech."""

    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    # Datos del cliente
    client_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    client_cedula: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    client_phone: Mapped[str] = mapped_column(String(60), default="")
    client_address: Mapped[str] = mapped_column(String(250), default="")

    # Datos físicos de la laptop
    laptop_model: Mapped[str] = mapped_column(String(160), nullable=False, default="Laptop")
    laptop_serial: Mapped[str] = mapped_column(String(100), default="", index=True)
    hardware_id: Mapped[str] = mapped_column(String(120), default="")
    hostname: Mapped[str] = mapped_column(String(120), default="")

    # Credenciales de instalación y criptografía offline
    enrollment_code: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, default=generate_enrollment_code
    )
    device_secret: Mapped[str] = mapped_column(
        String(64), nullable=False, default=generate_device_secret
    )
    agent_token: Mapped[str] = mapped_column(String(64), default="", index=True)

    # Control de bloqueo desde el servidor:
    # 'auto'     -> automático según vencimiento de cuotas
    # 'locked'   -> bloqueado forzosamente desde el servidor
    # 'unlocked' -> desbloqueado forzosamente / crédito liberado
    manual_status: Mapped[str] = mapped_column(String(20), default="auto")
    manual_unlock_until: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    lock_reason_override: Mapped[str] = mapped_column(String(300), default="")

    # Telemetría reportada por la laptop
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_reported_locked: Mapped[int] = mapped_column(Integer, default=0)
    last_ip: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    installments: Mapped[list["Installment"]] = relationship(
        "Installment",
        back_populates="device",
        cascade="all, delete-orphan",
        order_by="Installment.number",
    )
    events: Mapped[list["DeviceEvent"]] = relationship(
        "DeviceEvent",
        back_populates="device",
        cascade="all, delete-orphan",
        order_by="DeviceEvent.created_at.desc()",
    )


class Installment(Base):
    """Cuota de pago asociada a una laptop financiada."""

    __tablename__ = "installments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # 'pending' | 'paid'
    paid_at: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    notes: Mapped[str] = mapped_column(String(200), default="")

    device: Mapped["Device"] = relationship("Device", back_populates="installments")


class DeviceEvent(Base):
    """Bitácora de eventos del equipo y acciones del administrador."""

    __tablename__ = "device_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    device: Mapped["Device"] = relationship("Device", back_populates="events")


# Configuración del motor de base de datos
_ENGINE = None
_SessionLocal: Optional[sessionmaker] = None


def get_db_url() -> str:
    env_url = os.environ.get("CREDITECH_SERVER_DB") or os.environ.get("DATABASE_URL")
    if env_url:
        if env_url.startswith("postgres://"):
            env_url = env_url.replace("postgres://", "postgresql://", 1)
        return env_url
    data_dir = os.environ.get("CREDITECH_DATA_DIR", ".")
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "creditech_server.db")
    return f"sqlite:///{db_path}"


def init_server_db(db_url: str | None = None) -> sessionmaker:
    """Inicializa la base de datos del servidor y retorna la fábrica de sesiones."""
    global _ENGINE, _SessionLocal
    url = db_url or get_db_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    _ENGINE = create_engine(url, connect_args=connect_args, future=True)
    Base.metadata.create_all(_ENGINE)
    _SessionLocal = sessionmaker(bind=_ENGINE, expire_on_commit=False, class_=Session)
    return _SessionLocal


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        init_server_db()
    assert _SessionLocal is not None
    return _SessionLocal()


def generate_installment_schedule(
    first_due_date: date,
    total_installments: int,
    installment_amount: float,
    frequency_days: int = 30,
) -> list[dict]:
    """Genera un cronograma de cuotas consecutivas."""
    schedule = []
    for idx in range(1, max(1, int(total_installments)) + 1):
        if frequency_days == 30:
            # Sumar meses preservando el día aproximado o intervalos de 30 días
            due = first_due_date + timedelta(days=30 * (idx - 1))
        else:
            due = first_due_date + timedelta(days=frequency_days * (idx - 1))
        schedule.append(
            {
                "number": idx,
                "due_date": due.isoformat(),
                "amount": round(float(installment_amount), 2),
                "status": "pending",
            }
        )
    return schedule
