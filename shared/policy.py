"""Evaluación del estado de pago, avisos (1 día antes) y bloqueo por mora.

Este módulo contiene la lógica pura compartida entre el servidor y el agente
instalado en cada laptop para determinar en cualquier momento:
- Cuál es la próxima cuota pendiente.
- Si corresponde mostrar el **Aviso de Pago** (exactamente 1 día antes del
  vencimiento o el mismo día del vencimiento antes de entrar en mora).
- Si corresponde **Bloquear el equipo** (cuando una cuota pendiente ya venció,
  o cuando el administrador activó el bloqueo manual desde el servidor).
- Si el administrador otorgó un desbloqueo manual/temporal o si el cliente
  ingresó un PIN offline válido.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta


def generate_installment_schedule(
    first_due_date: date,
    total_installments: int,
    installment_amount: float,
    frequency_days: int = 30,
) -> list[dict]:
    """Genera un cronograma de cuotas consecutivas."""
    schedule = []
    for idx in range(1, max(1, int(total_installments)) + 1):
        due = first_due_date + timedelta(days=int(frequency_days) * (idx - 1))
        schedule.append(
            {
                "number": idx,
                "due_date": due.isoformat(),
                "amount": round(float(installment_amount), 2),
                "status": "pending",
            }
        )
    return schedule


def parse_iso_date(val: str | date | None) -> date | None:
    """Convierte una cadena YYYY-MM-DD o date en un objeto `date`."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    s = str(val).strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def evaluate_device_policy(
    installments: list[dict],
    manual_status: str = "auto",
    manual_unlock_until: str | date | None = None,
    lock_reason_override: str = "",
    today: date | None = None,
    reminder_days_before: int = 1,
) -> dict:
    """Evalúa si el equipo debe estar desbloqueado, con aviso de pago o bloqueado.

    Parámetros:
        installments: Lista de diccionarios con cuotas:
            - `number` (int): Número de cuota (1..N)
            - `due_date` (str YYYY-MM-DD | date): Fecha de vencimiento
            - `amount` (float): Monto de la cuota
            - `status` (str): 'pending' | 'paid'
        manual_status:
            - 'auto': Se rige automáticamente por las fechas de vencimiento.
            - 'locked': Bloqueado forzosamente desde el servidor por el administrador.
            - 'unlocked': Desbloqueado forzosamente o crédito finalizado/liberado.
        manual_unlock_until: Fecha (YYYY-MM-DD) hasta la cual un desbloqueo temporal
            (por servidor o por PIN offline) mantiene el equipo desbloqueado aunque
            exista una cuota vencida.
        lock_reason_override: Mensaje personalizado del administrador al bloquear.
        today: Fecha de evaluación (por defecto `date.today()`).
        reminder_days_before: Días de anticipación para mostrar aviso (por defecto 1 día antes).

    Retorna un diccionario con:
        - `locked` (bool): True si la laptop debe bloquearse a pantalla completa.
        - `lock_reason` (str): Motivo claro en español para mostrar en pantalla.
        - `warning_due_soon` (bool): True si debe mostrarse el aviso preventivo
          (1 día antes del vencimiento o el día de vencimiento).
        - `warning_message` (str): Texto del aviso de pago.
        - `days_until_due` (int | None): Días restantes para la próxima cuota
          (negativo si está vencida).
        - `next_installment` (dict | None): Próxima cuota pendiente.
        - `overdue_installments` (list[dict]): Cuotas vencidas no pagadas.
        - `pending_count` (int): Total de cuotas pendientes.
        - `paid_count` (int): Total de cuotas pagadas.
        - `total_count` (int): Total de cuotas del crédito.
    """
    ref_today = today or date.today()
    unlock_until_date = parse_iso_date(manual_unlock_until)
    has_active_grace = (
        unlock_until_date is not None and unlock_until_date >= ref_today
    )

    normalized: list[dict] = []
    for item in installments or []:
        due_d = parse_iso_date(item.get("due_date"))
        if due_d is None:
            continue
        normalized.append(
            {
                "id": item.get("id"),
                "number": int(item.get("number", 1)),
                "due_date": due_d.isoformat(),
                "_due_date_obj": due_d,
                "amount": float(item.get("amount", 0.0)),
                "status": str(item.get("status", "pending")).lower(),
                "paid_at": item.get("paid_at"),
            }
        )

    normalized.sort(key=lambda x: (x["_due_date_obj"], x["number"]))

    pending = [i for i in normalized if i["status"] != "paid"]
    paid = [i for i in normalized if i["status"] == "paid"]
    overdue = [i for i in pending if i["_due_date_obj"] < ref_today]

    next_inst = pending[0] if pending else None
    days_until_due: int | None = None
    if next_inst is not None:
        days_until_due = (next_inst["_due_date_obj"] - ref_today).days

    # Limpiar campo interno antes de exponer
    for item in normalized:
        item.pop("_due_date_obj", None)

    # 1. Bloqueo manual forzado por el administrador desde el servidor
    if manual_status == "locked" and not has_active_grace:
        reason = (
            lock_reason_override.strip()
            if lock_reason_override and lock_reason_override.strip()
            else "Equipo bloqueado remotamente por la administración de Creditech."
        )
        return {
            "locked": True,
            "lock_reason": reason,
            "warning_due_soon": False,
            "warning_message": "",
            "days_until_due": days_until_due,
            "next_installment": next_inst,
            "overdue_installments": overdue,
            "pending_count": len(pending),
            "paid_count": len(paid),
            "total_count": len(normalized),
        }

    # 2. Desbloqueo manual permanente / equipo liberado
    if manual_status == "unlocked":
        warning_due = False
        warning_msg = ""
        if (
            next_inst is not None
            and days_until_due is not None
            and 0 <= days_until_due <= reminder_days_before
        ):
            warning_due = True
            warning_msg = _build_warning_message(next_inst, days_until_due)
        return {
            "locked": False,
            "lock_reason": "",
            "warning_due_soon": warning_due,
            "warning_message": warning_msg,
            "days_until_due": days_until_due,
            "next_installment": next_inst,
            "overdue_installments": overdue,
            "pending_count": len(pending),
            "paid_count": len(paid),
            "total_count": len(normalized),
        }

    # 3. Modo automático ('auto'): verificar si hay cuotas vencidas
    if overdue and not has_active_grace:
        first_overdue = overdue[0]
        days_late = (ref_today - date.fromisoformat(first_overdue["due_date"])).days
        reason = (
            lock_reason_override.strip()
            if lock_reason_override and lock_reason_override.strip()
            else (
                f"Cuota #{first_overdue['number']} vencida el {first_overdue['due_date']} "
                f"(${first_overdue['amount']:.2f} — {days_late} día(s) de atraso). "
                "Comuníquese con Creditech para registrar su pago y desbloquear el equipo."
            )
        )
        return {
            "locked": True,
            "lock_reason": reason,
            "warning_due_soon": False,
            "warning_message": "",
            "days_until_due": days_until_due,
            "next_installment": next_inst,
            "overdue_installments": overdue,
            "pending_count": len(pending),
            "paid_count": len(paid),
            "total_count": len(normalized),
        }

    # 4. No está bloqueado: verificar si corresponde aviso 1 día antes (o hoy mismo)
    warning_due = False
    warning_msg = ""
    if (
        next_inst is not None
        and days_until_due is not None
        and 0 <= days_until_due <= reminder_days_before
    ):
        warning_due = True
        warning_msg = _build_warning_message(next_inst, days_until_due)

    return {
        "locked": False,
        "lock_reason": "",
        "warning_due_soon": warning_due,
        "warning_message": warning_msg,
        "days_until_due": days_until_due,
        "next_installment": next_inst,
        "overdue_installments": overdue,
        "pending_count": len(pending),
        "paid_count": len(paid),
        "total_count": len(normalized),
    }


def _build_warning_message(installment: dict, days_until_due: int) -> str:
    """Construye el mensaje en español para el aviso preventivo de pago."""
    num = installment["number"]
    due = installment["due_date"]
    amount = installment["amount"]
    if days_until_due == 1:
        return (
            f"AVISO DE PAGO CREDITECH: Su cuota #{num} por ${amount:.2f} "
            f"vence MAÑANA ({due}). Realice su pago a tiempo para evitar el "
            "bloqueo automático de este equipo."
        )
    if days_until_due == 0:
        return (
            f"AVISO DE PAGO CREDITECH: Su cuota #{num} por ${amount:.2f} "
            f"vence HOY ({due}). Recuerde reportar su pago hoy para evitar el "
            "bloqueo automático del equipo."
        )
    return (
        f"AVISO DE PAGO CREDITECH: Su cuota #{num} por ${amount:.2f} "
        f"vence en {days_until_due} días ({due})."
    )
