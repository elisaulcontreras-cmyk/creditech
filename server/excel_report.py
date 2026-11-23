"""Generador de Reportes Excel (.xlsx) de Cartera y Deudores para Creditech by indatech.

Genera un archivo Excel profesional con formato corporativo (`indatech.` #00D094 y #071D20)
con tres hojas:
1. `Personas que Deben`: Lista exclusiva de clientes con saldo pendiente (> $0.00),
   mostrando Nombre, Cédula, Teléfono, Laptop/Serial, Total Financiado, Total Pagado,
   Total que Falta por Pagar (Deuda), Cuotas Pagadas/Pendientes/Vencidas, Próximo Vencimiento
   y Estado del Equipo, más fila de Totales.
2. `Resumen General`: Todos los clientes (tanto los que deben como los que ya terminaron
   de pagar su crédito) para respaldo completo.
3. `Detalle de Cuotas`: Desglose cuota por cuota de cada cliente con fechas de vencimiento,
   montos, estado (PAGADA / PENDIENTE / VENCIDA) y fecha de pago.
"""

from __future__ import annotations

import io
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import xlsxwriter

from server.models import Device
from shared.policy import evaluate_device_policy


def build_excel_report_bytes(
    devices: Iterable[Device],
    today: date | None = None,
) -> bytes:
    """Construye el archivo Excel (.xlsx) en memoria y retorna sus bytes."""
    ref_today = today or date.today()
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    # Formatos corporativos Creditech by indatech.
    title_fmt = workbook.add_format(
        {
            "bold": True,
            "font_size": 15,
            "font_color": "#FFFFFF",
            "bg_color": "#071D20",
            "align": "left",
            "valign": "vcenter",
        }
    )
    subtitle_fmt = workbook.add_format(
        {
            "bold": True,
            "font_size": 10,
            "font_color": "#00D094",
            "bg_color": "#071D20",
            "align": "left",
            "valign": "vcenter",
        }
    )
    header_fmt = workbook.add_format(
        {
            "bold": True,
            "font_size": 10,
            "font_color": "#071D20",
            "bg_color": "#00D094",
            "border": 1,
            "border_color": "#071D20",
            "align": "center",
            "valign": "vcenter",
            "text_wrap": True,
        }
    )
    cell_fmt = workbook.add_format(
        {
            "font_size": 10,
            "border": 1,
            "border_color": "#D9E8E5",
            "valign": "vcenter",
        }
    )
    cell_center_fmt = workbook.add_format(
        {
            "font_size": 10,
            "border": 1,
            "border_color": "#D9E8E5",
            "align": "center",
            "valign": "vcenter",
        }
    )
    money_fmt = workbook.add_format(
        {
            "font_size": 10,
            "num_format": "$#,##0.00",
            "border": 1,
            "border_color": "#D9E8E5",
            "valign": "vcenter",
        }
    )
    money_paid_fmt = workbook.add_format(
        {
            "font_size": 10,
            "bold": True,
            "font_color": "#008F64",
            "bg_color": "#E6FBF4",
            "num_format": "$#,##0.00",
            "border": 1,
            "border_color": "#D9E8E5",
            "valign": "vcenter",
        }
    )
    money_debt_fmt = workbook.add_format(
        {
            "font_size": 10,
            "bold": True,
            "font_color": "#C92A2A",
            "bg_color": "#FFF5F5",
            "num_format": "$#,##0.00",
            "border": 1,
            "border_color": "#D9E8E5",
            "valign": "vcenter",
        }
    )
    status_locked_fmt = workbook.add_format(
        {
            "font_size": 10,
            "bold": True,
            "font_color": "#C92A2A",
            "bg_color": "#FFF5F5",
            "border": 1,
            "border_color": "#D9E8E5",
            "align": "center",
            "valign": "vcenter",
        }
    )
    status_warn_fmt = workbook.add_format(
        {
            "font_size": 10,
            "bold": True,
            "font_color": "#B45309",
            "bg_color": "#FFFBEB",
            "border": 1,
            "border_color": "#D9E8E5",
            "align": "center",
            "valign": "vcenter",
        }
    )
    status_ok_fmt = workbook.add_format(
        {
            "font_size": 10,
            "bold": True,
            "font_color": "#008F64",
            "bg_color": "#E6FBF4",
            "border": 1,
            "border_color": "#D9E8E5",
            "align": "center",
            "valign": "vcenter",
        }
    )
    total_label_fmt = workbook.add_format(
        {
            "bold": True,
            "font_size": 11,
            "font_color": "#FFFFFF",
            "bg_color": "#071D20",
            "border": 1,
            "align": "right",
            "valign": "vcenter",
        }
    )
    total_money_fmt = workbook.add_format(
        {
            "bold": True,
            "font_size": 11,
            "font_color": "#00D094",
            "bg_color": "#071D20",
            "num_format": "$#,##0.00",
            "border": 1,
            "valign": "vcenter",
        }
    )

    # Preprocesar datos financieros por cliente/equipo
    all_rows = []
    debtor_rows = []
    installment_rows = []

    for dev in devices:
        inst_sorted = sorted(dev.installments, key=lambda x: x.number)
        inst_dicts = [
            {
                "id": i.id,
                "number": i.number,
                "due_date": i.due_date,
                "amount": float(i.amount),
                "status": i.status,
                "paid_at": i.paid_at,
            }
            for i in inst_sorted
        ]
        policy = evaluate_device_policy(
            installments=inst_dicts,
            manual_status=dev.manual_status,
            manual_unlock_until=dev.manual_unlock_until,
            lock_reason_override=dev.lock_reason_override,
            today=ref_today,
        )

        total_amount = round(sum(i["amount"] for i in inst_dicts), 2)
        paid_amount = round(
            sum(i["amount"] for i in inst_dicts if i["status"] == "paid"), 2
        )
        pending_amount = round(total_amount - paid_amount, 2)

        next_due = (
            policy["next_installment"]["due_date"]
            if policy["next_installment"]
            else "PAGADO"
        )
        overdue_count = len(policy["overdue_installments"])

        if policy["locked"]:
            status_str = "BLOQUEADO"
        elif policy["warning_due_soon"]:
            status_str = "AVISO 1 DÍA ANTES"
        elif pending_amount <= 0:
            status_str = "SOLVENTE / PAGADO"
        else:
            status_str = "ACTIVO / AL DÍA"

        summary = {
            "client_name": dev.client_name,
            "client_cedula": dev.client_cedula,
            "client_phone": dev.client_phone or "N/A",
            "laptop_model": dev.laptop_model,
            "laptop_serial": dev.laptop_serial or "N/A",
            "enrollment_code": dev.enrollment_code,
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "pending_amount": pending_amount,
            "paid_count": policy["paid_count"],
            "pending_count": policy["pending_count"],
            "total_count": policy["total_count"],
            "overdue_count": overdue_count,
            "next_due": next_due,
            "status_str": status_str,
            "locked": policy["locked"],
            "warning": policy["warning_due_soon"],
        }
        all_rows.append(summary)
        if pending_amount > 0.001:
            debtor_rows.append(summary)

        for inst in inst_dicts:
            is_paid = inst["status"] == "paid"
            if is_paid:
                inst_state = "PAGADA"
            elif inst["due_date"] < ref_today.isoformat():
                inst_state = "VENCIDA (EN MORA)"
            else:
                inst_state = "PENDIENTE"

            installment_rows.append(
                {
                    "client_name": dev.client_name,
                    "client_cedula": dev.client_cedula,
                    "laptop_model": dev.laptop_model,
                    "enrollment_code": dev.enrollment_code,
                    "number": inst["number"],
                    "due_date": inst["due_date"],
                    "amount": inst["amount"],
                    "inst_state": inst_state,
                    "paid_at": (inst["paid_at"] or "")[:10] if is_paid else "-",
                }
            )

    def _write_summary_sheet(sheet_name: str, title_text: str, rows_data: list[dict]) -> None:
        ws = workbook.add_worksheet(sheet_name)
        ws.hide_gridlines(2)

        headers = [
            "Nombre del Cliente",
            "Número de Cédula",
            "Teléfono",
            "Laptop / Modelo",
            "Serial",
            "Código Creditech",
            "Total Crédito ($)",
            "Lo que ha Pagado ($)",
            "Lo que Falta por Pagar ($)",
            "Cuotas Pagadas",
            "Cuotas Pendientes",
            "Cuotas Vencidas",
            "Próximo Vencimiento",
            "Estado del Equipo",
        ]

        # Banner superior
        ws.merge_range(0, 0, 0, len(headers) - 1, title_text, title_fmt)
        ws.set_row(0, 28)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        ws.merge_range(
            1,
            0,
            1,
            len(headers) - 1,
            f"CREDITECH by indatech. — Respaldo Oficial de Cartera · Generado el {now_str}",
            subtitle_fmt,
        )
        ws.set_row(1, 20)

        # Cabeceras de tabla en fila 3 (índice 3)
        header_row = 3
        ws.set_row(header_row, 26)
        for col_idx, h_text in enumerate(headers):
            ws.write(header_row, col_idx, h_text, header_fmt)

        # Anchos de columna
        col_widths = [26, 16, 16, 22, 15, 16, 16, 18, 20, 14, 15, 14, 17, 18]
        for col_idx, width in enumerate(col_widths):
            ws.set_column(col_idx, col_idx, width)

        sum_total = 0.0
        sum_paid = 0.0
        sum_pending = 0.0

        row_cursor = header_row + 1
        for item in rows_data:
            ws.set_row(row_cursor, 21)
            ws.write(row_cursor, 0, item["client_name"], cell_fmt)
            ws.write(row_cursor, 1, item["client_cedula"], cell_center_fmt)
            ws.write(row_cursor, 2, item["client_phone"], cell_center_fmt)
            ws.write(row_cursor, 3, item["laptop_model"], cell_fmt)
            ws.write(row_cursor, 4, item["laptop_serial"], cell_center_fmt)
            ws.write(row_cursor, 5, item["enrollment_code"], cell_center_fmt)
            ws.write_number(row_cursor, 6, item["total_amount"], money_fmt)
            ws.write_number(row_cursor, 7, item["paid_amount"], money_paid_fmt)
            ws.write_number(
                row_cursor,
                8,
                item["pending_amount"],
                money_debt_fmt if item["pending_amount"] > 0 else money_paid_fmt,
            )
            ws.write(
                row_cursor,
                9,
                f"{item['paid_count']} / {item['total_count']}",
                cell_center_fmt,
            )
            ws.write_number(row_cursor, 10, item["pending_count"], cell_center_fmt)
            ws.write_number(row_cursor, 11, item["overdue_count"], cell_center_fmt)
            ws.write(row_cursor, 12, item["next_due"], cell_center_fmt)

            if item["locked"]:
                st_fmt = status_locked_fmt
            elif item["warning"]:
                st_fmt = status_warn_fmt
            else:
                st_fmt = status_ok_fmt
            ws.write(row_cursor, 13, item["status_str"], st_fmt)

            sum_total += item["total_amount"]
            sum_paid += item["paid_amount"]
            sum_pending += item["pending_amount"]
            row_cursor += 1

        # Fila de totales
        ws.set_row(row_cursor, 24)
        ws.merge_range(
            row_cursor,
            0,
            row_cursor,
            5,
            f"TOTALES ({len(rows_data)} cliente(s)):",
            total_label_fmt,
        )
        ws.write_number(row_cursor, 6, round(sum_total, 2), total_money_fmt)
        ws.write_number(row_cursor, 7, round(sum_paid, 2), total_money_fmt)
        ws.write_number(row_cursor, 8, round(sum_pending, 2), total_money_fmt)
        ws.merge_range(row_cursor, 9, row_cursor, 13, "", total_label_fmt)

    # Hoja 1: Personas que Deben Dinero (Deudores con saldo pendiente > 0)
    _write_summary_sheet(
        sheet_name="Personas que Deben",
        title_text="LISTA DE CLIENTES CON SALDO PENDIENTE (DEUDORES)",
        rows_data=debtor_rows,
    )

    # Hoja 2: Resumen General de Todos los Clientes
    _write_summary_sheet(
        sheet_name="Resumen General",
        title_text="RESUMEN GENERAL DE TODOS LOS CLIENTES Y EQUIPOS",
        rows_data=all_rows,
    )

    # Hoja 3: Detalle de Cuotas
    ws_inst = workbook.add_worksheet("Detalle de Cuotas")
    ws_inst.hide_gridlines(2)
    inst_headers = [
        "Nombre del Cliente",
        "Número de Cédula",
        "Laptop",
        "Código Creditech",
        "Nº Cuota",
        "Fecha Vencimiento",
        "Monto Cuota ($)",
        "Estado de Cuota",
        "Fecha de Pago",
    ]
    ws_inst.merge_range(
        0,
        0,
        0,
        len(inst_headers) - 1,
        "HISTORIAL DETALLADO DE CUOTAS POR CLIENTE",
        title_fmt,
    )
    ws_inst.set_row(0, 28)
    ws_inst.merge_range(
        1,
        0,
        1,
        len(inst_headers) - 1,
        "CREDITECH by indatech. — Desglose de pagos realizados y cuotas por cobrar",
        subtitle_fmt,
    )
    ws_inst.set_row(1, 20)

    ws_inst.set_row(3, 25)
    for col_idx, h_text in enumerate(inst_headers):
        ws_inst.write(3, col_idx, h_text, header_fmt)

    inst_widths = [26, 16, 22, 16, 11, 17, 16, 18, 16]
    for col_idx, w in enumerate(inst_widths):
        ws_inst.set_column(col_idx, col_idx, w)

    r_idx = 4
    for ir in installment_rows:
        ws_inst.set_row(r_idx, 20)
        ws_inst.write(r_idx, 0, ir["client_name"], cell_fmt)
        ws_inst.write(r_idx, 1, ir["client_cedula"], cell_center_fmt)
        ws_inst.write(r_idx, 2, ir["laptop_model"], cell_fmt)
        ws_inst.write(r_idx, 3, ir["enrollment_code"], cell_center_fmt)
        ws_inst.write(r_idx, 4, f"Cuota #{ir['number']}", cell_center_fmt)
        ws_inst.write(r_idx, 5, ir["due_date"], cell_center_fmt)
        ws_inst.write_number(r_idx, 6, ir["amount"], money_fmt)

        if ir["inst_state"] == "PAGADA":
            st_f = status_ok_fmt
        elif "VENCIDA" in ir["inst_state"]:
            st_f = status_locked_fmt
        else:
            st_f = status_warn_fmt
        ws_inst.write(r_idx, 7, ir["inst_state"], st_f)
        ws_inst.write(r_idx, 8, ir["paid_at"], cell_center_fmt)
        r_idx += 1

    workbook.close()
    return output.getvalue()


def save_automatic_excel_backup(devices: Iterable[Device], backup_dir: str | Path = "respaldos") -> Path:
    """Guarda automáticamente una copia del Excel de respaldo en el disco del servidor."""
    folder = Path(backup_dir)
    folder.mkdir(parents=True, exist_ok=True)
    xlsx_bytes = build_excel_report_bytes(devices)
    latest_path = folder / "respaldo_deudores_creditech.xlsx"
    latest_path.write_bytes(xlsx_bytes)
    return latest_path
