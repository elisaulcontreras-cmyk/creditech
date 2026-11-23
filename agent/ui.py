"""Interfaz gráfica moderna en PyQt6 para el Agente de Laptop Creditech by indatech.

Incluye el logo oficial de `indatech.` (renderizado nativamente en alta definición
con QPainter y antialiasing sobre el isotipo metaball `#00D094`) y una estética
moderna en todas las pantallas:
1. `IndatechLogoWidget`: Renderizador vectorial nativo del logo de `indatech.`
2. `EnrollmentDialog`: Asistente moderno de instalación y registro con Nombre y Cédula.
3. `PaymentReminderDialog`: Ventana emergente de **Aviso de Pago 1 día antes** del vencimiento.
4. `FullScreenLockWindow`: Pantalla de **Bloqueo Total** con el logo de Indatech,
   Nombre y Número de Cédula del cliente, verificación online y desbloqueo por PIN offline.
5. `ClientPortalWindow`: Ventana principal con el logo de Indatech, estado del crédito,
   datos del titular y tabla de cuotas.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Callable, Optional

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import (
    QBrush,
    QCloseEvent,
    QColor,
    QFont,
    QIcon,
    QKeyEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from agent.startup import install_windows_startup
from agent.state import AgentStateManager


def render_indatech_logo_pixmap(
    size: int = 96,
    show_text: bool = True,
    bg_color: str = "#FFFFFF",
) -> QPixmap:
    """Renderiza el logo oficial de `indatech.` en un QPixmap de alta resolución."""
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

    scale = size / 420.0
    p.scale(scale, scale)

    # Fondo redondeado
    bg_path = QPainterPath()
    bg_path.addRoundedRect(QRectF(4, 4, 412, 412), 68, 68)
    p.fillPath(bg_path, QColor(bg_color))

    emerald = QColor("#00D094")
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(emerald))

    # Si no se muestra el texto "indatech.", centramos verticalmente el isotipo
    if not show_text:
        p.translate(5, 36)

    def draw_metaball_bone(x1: float, y1: float, r1: float, x2: float, y2: float, r2: float, neck_w: float) -> None:
        """Dibuja dos nodos circulares unidos por un puente cóncavo suave (efecto metaball)."""
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(emerald))
        p.drawEllipse(QPointF(x1, y1), r1, r1)
        p.drawEllipse(QPointF(x2, y2), r2, r2)
        pen = QPen(emerald, neck_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    # 1. Pieza superior en L invertida: (158,72) -> (236,72) -> (236,144)
    draw_metaball_bone(158, 72, 27, 236, 72, 27, 28)
    draw_metaball_bone(236, 72, 27, 236, 144, 25, 27)

    # 2. Punto suelto arriba a la derecha
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(emerald))
    p.drawEllipse(QPointF(312, 72), 26, 26)

    # 3. Punto suelto a la izquierda media
    p.drawEllipse(QPointF(92, 166), 25, 25)

    # 4. Pieza vertical media izquierda: (158,140) -> (158,214)
    draw_metaball_bone(158, 140, 26, 158, 214, 26, 30)

    # 5. Pieza inferior escalonada: (158,278) -> (236,278) -> (236,214) -> (296,154)
    draw_metaball_bone(158, 278, 27, 236, 278, 26, 26)
    draw_metaball_bone(236, 278, 26, 236, 214, 25, 26)
    draw_metaball_bone(236, 214, 25, 296, 154, 27, 28)

    # 6. Punto suelto abajo a la derecha
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(emerald))
    p.drawEllipse(QPointF(302, 242), 25, 25)

    # 7. Logotipo inferior "indatech."
    if show_text:
        font = QFont("Segoe UI", 54, QFont.Weight.Black)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, -1.8)
        p.setFont(font)
        p.setPen(QPen(emerald))
        p.drawText(QRectF(10, 306, 400, 95), Qt.AlignmentFlag.AlignCenter, "indatech.")

    p.end()
    return pix


class IndatechLogoWidget(QLabel):
    """Widget que muestra el logo oficial de `indatech.` al tamaño indicado."""

    def __init__(
        self,
        size: int = 72,
        show_text: bool = True,
        bg_color: str = "#FFFFFF",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        pix = render_indatech_logo_pixmap(size=size * 2, show_text=show_text, bg_color=bg_color)
        pix.setDevicePixelRatio(2.0)
        self.setPixmap(pix)
        self.setScaledContents(True)


CREDITECH_QSS = """
QWidget {
    font-family: 'Segoe UI Variable Text', 'Segoe UI', Inter, sans-serif;
    font-size: 13px;
    color: #0F2327;
}
QMainWindow, QDialog {
    background-color: #F3F8F7;
}
QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #D9E8E5;
    border-radius: 16px;
}
QFrame#headerBanner {
    background-color: #071D20;
    border: 1px solid #00D094;
    border-radius: 16px;
}
QFrame#warningBanner {
    background-color: #FFFBEB;
    border: 2px solid #F59E0B;
    border-radius: 14px;
}
QFrame#lockCard {
    background-color: #FFFFFF;
    border: 2px solid #00D094;
    border-radius: 20px;
}
QLabel#brandTitle {
    color: #FFFFFF;
    font-size: 23px;
    font-weight: 900;
    letter-spacing: 0.4px;
}
QLabel#brandPill {
    background-color: rgba(0, 208, 148, 0.18);
    color: #00D094;
    border: 1px solid #00D094;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 12px;
    font-weight: 800;
}
QLabel#brandSub {
    color: #A3C2C6;
    font-size: 12.5px;
}
QLabel#sectionTitle {
    color: #071D20;
    font-size: 16px;
    font-weight: 800;
}
QLabel#clientInfoTitle {
    color: #071D20;
    font-size: 19px;
    font-weight: 900;
}
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #F8FBFA;
    border: 1.5px solid #CBE0DC;
    border-radius: 10px;
    padding: 9px 13px;
    font-size: 13.5px;
    color: #071D20;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 2px solid #00D094;
    background-color: #FFFFFF;
}
QTabWidget::pane {
    border: 1px solid #D9E8E5;
    border-radius: 12px;
    background: #FFFFFF;
}
QTabBar::tab {
    background: #E8F2F0;
    color: #526B70;
    padding: 10px 18px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    font-weight: 700;
    margin-right: 4px;
}
QTabBar::tab:selected {
    background: #00D094;
    color: #04221B;
    font-weight: 800;
}
QPushButton#primaryBtn {
    background-color: #00D094;
    color: #04221B;
    border: none;
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 800;
    font-size: 13.5px;
}
QPushButton#primaryBtn:hover {
    background-color: #00B580;
    color: #FFFFFF;
}
QPushButton#successBtn {
    background-color: #071D20;
    color: #00D094;
    border: 1.5px solid #00D094;
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 800;
}
QPushButton#successBtn:hover {
    background-color: #00D094;
    color: #04221B;
}
QPushButton#dangerBtn {
    background-color: #E03131;
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 800;
}
QPushButton#secondaryBtn {
    background-color: #FFFFFF;
    color: #0F2327;
    border: 1px solid #CBE0DC;
    border-radius: 10px;
    padding: 9px 16px;
    font-weight: 700;
}
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #D9E8E5;
    border-radius: 12px;
    gridline-color: #EBF3F1;
}
QHeaderView::section {
    background-color: #F4F9F8;
    color: #526B70;
    font-weight: 800;
    font-size: 11.5px;
    padding: 10px;
    border: none;
    border-bottom: 2px solid #D9E8E5;
}
"""


class EnrollmentDialog(QDialog):
    """Asistente moderno para instalar y vincular la laptop con Nombre y Cédula del cliente."""

    def __init__(self, state_mgr: AgentStateManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.state_mgr = state_mgr
        self.setWindowTitle("Creditech by indatech. — Instalación y Registro de Equipo")
        self.setWindowIcon(QIcon(render_indatech_logo_pixmap(64, show_text=False)))
        self.setMinimumWidth(580)
        self.setStyleSheet(CREDITECH_QSS)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(16)

        # Cabecera con Logo oficial Indatech
        banner = QFrame()
        banner.setObjectName("headerBanner")
        b_layout = QHBoxLayout(banner)
        b_layout.setContentsMargins(18, 16, 18, 16)
        b_layout.setSpacing(16)

        logo_w = IndatechLogoWidget(size=68, show_text=True)
        b_layout.addWidget(logo_w)

        title_col = QVBoxLayout()
        top_row = QHBoxLayout()
        title = QLabel("CREDITECH")
        title.setObjectName("brandTitle")
        pill = QLabel("by indatech.")
        pill.setObjectName("brandPill")
        top_row.addWidget(title)
        top_row.addWidget(pill)
        top_row.addStretch()

        sub = QLabel(
            "Vincule esta laptop al Servidor Central con el Nombre y Número de Cédula del cliente"
        )
        sub.setObjectName("brandSub")
        sub.setWordWrap(True)
        title_col.addLayout(top_row)
        title_col.addWidget(sub)
        b_layout.addLayout(title_col, 1)
        layout.addWidget(banner)

        # URL del servidor
        srv_card = QFrame()
        srv_card.setObjectName("card")
        srv_form = QFormLayout(srv_card)
        srv_form.setContentsMargins(18, 14, 18, 14)
        self.server_url_input = QLineEdit(
            self.state_mgr.state.get("server_url", "https://creditech-indatech.onrender.com")
        )
        self.server_url_input.setPlaceholderText("Ej: https://creditech-indatech.onrender.com")
        srv_form.addRow("Servidor Central:", self.server_url_input)
        layout.addWidget(srv_card)

        # Pestañas
        self.tabs = QTabWidget()

        # Tab 1: Registro directo con Nombre y Cédula
        tab_direct = QWidget()
        f_direct = QFormLayout(tab_direct)
        f_direct.setContentsMargins(18, 18, 18, 18)
        f_direct.setSpacing(11)

        self.client_name_input = QLineEdit()
        self.client_name_input.setPlaceholderText("Ej: Juan Carlos Gómez")
        self.client_cedula_input = QLineEdit()
        self.client_cedula_input.setPlaceholderText("Ej: V-19.348.210")
        self.client_phone_input = QLineEdit()
        self.client_phone_input.setPlaceholderText("Ej: +58 414-0000000")
        self.laptop_model_input = QLineEdit("Laptop Financiada Indatech")
        self.laptop_serial_input = QLineEdit()
        self.laptop_serial_input.setPlaceholderText("Serial del equipo (opcional)")

        tomorrow_iso = (date.today() + timedelta(days=1)).isoformat()
        self.first_due_input = QLineEdit(tomorrow_iso)
        self.first_due_input.setPlaceholderText("YYYY-MM-DD")

        self.installments_spin = QSpinBox()
        self.installments_spin.setRange(1, 48)
        self.installments_spin.setValue(6)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(1.0, 10000.0)
        self.amount_spin.setValue(85.00)
        self.amount_spin.setPrefix("$ ")

        f_direct.addRow("Nombre del Cliente *:", self.client_name_input)
        f_direct.addRow("Número de Cédula *:", self.client_cedula_input)
        f_direct.addRow("Teléfono:", self.client_phone_input)
        f_direct.addRow("Modelo de Laptop:", self.laptop_model_input)
        f_direct.addRow("Serial del Equipo:", self.laptop_serial_input)
        f_direct.addRow("Vencimiento 1ª Cuota:", self.first_due_input)
        f_direct.addRow("Cantidad de Cuotas:", self.installments_spin)
        f_direct.addRow("Monto por Cuota:", self.amount_spin)

        # Tab 2: Código de Instalación generado en el servidor
        tab_code = QWidget()
        f_code = QFormLayout(tab_code)
        f_code.setContentsMargins(18, 18, 18, 18)
        f_code.setSpacing(12)
        self.enrollment_code_input = QLineEdit()
        self.enrollment_code_input.setPlaceholderText("Ej: CRD-4829-9104")
        code_help = QLabel(
            "Si ya registró al cliente en el Panel Web del Servidor, pegue aquí el "
            "Código de Instalación (CRD-XXXX-XXXX) para sincronizar automáticamente "
            "su Nombre, Número de Cédula y cronograma de cuotas."
        )
        code_help.setWordWrap(True)
        f_code.addRow("Código de Instalación:", self.enrollment_code_input)
        f_code.addRow(code_help)

        self.tabs.addTab(tab_direct, "Registrar Nombre y Cédula Aquí")
        self.tabs.addTab(tab_code, "Vincular con Código del Servidor")
        layout.addWidget(self.tabs)

        self.startup_check = QCheckBox(
            "Iniciar Creditech automáticamente al encender Windows en esta laptop"
        )
        self.startup_check.setChecked(True)
        layout.addWidget(self.startup_check)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.submit_btn = QPushButton("✓ Activar Protección Creditech en este Equipo")
        self.submit_btn.setObjectName("primaryBtn")
        self.submit_btn.clicked.connect(self._on_enroll)
        btn_row.addWidget(self.submit_btn)
        layout.addLayout(btn_row)

    def _on_enroll(self) -> None:
        server_url = self.server_url_input.text().strip()
        use_code_tab = self.tabs.currentIndex() == 1
        code = self.enrollment_code_input.text().strip() if use_code_tab else ""
        name = self.client_name_input.text().strip()
        cedula = self.client_cedula_input.text().strip()

        if use_code_tab and not code:
            QMessageBox.warning(self, "Creditech", "Ingrese el Código de Instalación (CRD-XXXX-XXXX).")
            return
        if not use_code_tab and (not name or not cedula):
            QMessageBox.warning(
                self,
                "Creditech",
                "Debe ingresar obligatoriamente el Nombre Completo y el Número de Cédula del cliente.",
            )
            return

        try:
            if server_url:
                self.state_mgr.enroll_with_server(
                    server_url=server_url,
                    enrollment_code=code,
                    client_name=name,
                    client_cedula=cedula,
                    client_phone=self.client_phone_input.text().strip(),
                    laptop_model=self.laptop_model_input.text().strip(),
                    laptop_serial=self.laptop_serial_input.text().strip(),
                    first_due_date=self.first_due_input.text().strip(),
                    total_installments=self.installments_spin.value(),
                    installment_amount=self.amount_spin.value(),
                )
            else:
                self.state_mgr.enroll_standalone_local(
                    client_name=name,
                    client_cedula=cedula,
                    client_phone=self.client_phone_input.text().strip(),
                    laptop_model=self.laptop_model_input.text().strip(),
                    laptop_serial=self.laptop_serial_input.text().strip(),
                    first_due_date=self.first_due_input.text().strip(),
                    total_installments=self.installments_spin.value(),
                    installment_amount=self.amount_spin.value(),
                )
        except Exception as exc:
            if not use_code_tab and name and cedula:
                # Si el servidor no está activo o no hay red, activar en Modo Autónomo por Cédula/PIN
                self.state_mgr.enroll_standalone_local(
                    client_name=name,
                    client_cedula=cedula,
                    client_phone=self.client_phone_input.text().strip(),
                    laptop_model=self.laptop_model_input.text().strip(),
                    laptop_serial=self.laptop_serial_input.text().strip(),
                    first_due_date=self.first_due_input.text().strip(),
                    total_installments=self.installments_spin.value(),
                    installment_amount=self.amount_spin.value(),
                    server_url=server_url,
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error de Conexión con el Servidor",
                    f"No se pudo vincular con el servidor ({server_url}):\n{exc}",
                )
                return

        if self.startup_check.isChecked():
            install_windows_startup()
        QMessageBox.information(
            self,
            "Creditech by indatech. — Equipo Vinculado",
            f"Equipo registrado correctamente a nombre de:\n"
            f"Cliente: {self.state_mgr.state['client_name']}\n"
            f"Cédula: {self.state_mgr.state['client_cedula']}\n"
            f"Código de Equipo: {self.state_mgr.state['enrollment_code']}",
        )
        self.accept()


class PaymentReminderDialog(QDialog):
    """Ventana emergente moderna de Aviso de Pago que aparece 1 día antes del vencimiento."""

    def __init__(
        self,
        client_name: str,
        client_cedula: str,
        warning_message: str,
        next_installment: Optional[dict],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Creditech by indatech. — Aviso de Próximo Vencimiento")
        self.setWindowIcon(QIcon(render_indatech_logo_pixmap(64, show_text=False)))
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
        )
        self.setMinimumWidth(540)
        self.setStyleSheet(CREDITECH_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        top_bar = QHBoxLayout()
        top_bar.addWidget(IndatechLogoWidget(size=58, show_text=True))
        t_col = QVBoxLayout()
        badge = QLabel("⚠️ AVISO PREVENTIVO DE PAGO (1 DÍA ANTES)")
        badge.setStyleSheet("color: #D97706; font-weight: 900; font-size: 15px;")
        sub_b = QLabel("Creditech by indatech. — Recordatorio de Cuota")
        sub_b.setStyleSheet("color: #526B70; font-size: 12.5px; font-weight: 600;")
        t_col.addWidget(badge)
        t_col.addWidget(sub_b)
        top_bar.addLayout(t_col, 1)
        layout.addLayout(top_bar)

        card = QFrame()
        card.setObjectName("warningBanner")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(18, 18, 18, 18)
        c_layout.setSpacing(10)

        client_lbl = QLabel(
            f"Titular: <b>{client_name}</b> &nbsp;|&nbsp; Cédula: <b>{client_cedula}</b>"
        )
        client_lbl.setStyleSheet("font-size: 14px; color: #071D20;")
        c_layout.addWidget(client_lbl)

        msg_lbl = QLabel(warning_message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #78350F;")
        c_layout.addWidget(msg_lbl)

        if next_installment:
            detail_lbl = QLabel(
                f"• Cuota #{next_installment['number']}\n"
                f"• Fecha de Vencimiento: {next_installment['due_date']}\n"
                f"• Monto a Pagar: ${float(next_installment['amount']):.2f}"
            )
            detail_lbl.setStyleSheet("font-size: 13.5px; font-weight: 700; color: #071D20;")
            c_layout.addWidget(detail_lbl)

        layout.addWidget(card)

        btn = QPushButton("Entendido, realizaré el pago a tiempo")
        btn.setObjectName("primaryBtn")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)


class FullScreenLockWindow(QWidget):
    """Pantalla de bloqueo total moderna con el logo de Indatech cuando el cliente no paga."""

    def __init__(
        self,
        state_mgr: AgentStateManager,
        on_unlocked_callback: Callable[[], None],
    ) -> None:
        super().__init__(None)
        self.state_mgr = state_mgr
        self.on_unlocked_callback = on_unlocked_callback
        self._allow_close = False

        self.setWindowTitle("CREDITECH BY INDATECH — EQUIPO BLOQUEADO")
        self.setWindowIcon(QIcon(render_indatech_logo_pixmap(64, show_text=False)))
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet(
            CREDITECH_QSS
            + """
            QWidget#lockRoot {
                background-color: #071D20;
            }
            """
        )
        self.setObjectName("lockRoot")
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(40, 40, 40, 40)
        root_layout.addStretch(1)

        center_row = QHBoxLayout()
        center_row.addStretch(1)

        card = QFrame()
        card.setObjectName("lockCard")
        card.setFixedWidth(660)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(36, 30, 36, 30)
        c_layout.setSpacing(14)

        # Logo centrado arriba
        logo_row = QHBoxLayout()
        logo_row.addStretch()
        logo_row.addWidget(IndatechLogoWidget(size=96, show_text=True))
        logo_row.addStretch()
        c_layout.addLayout(logo_row)

        header_lbl = QLabel("🔒 EQUIPO BLOQUEADO — CREDITECH")
        header_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_lbl.setStyleSheet(
            "color: #E03131; font-size: 24px; font-weight: 900; letter-spacing: 0.6px;"
        )
        c_layout.addWidget(header_lbl)

        sub_lbl = QLabel(
            "El uso de esta laptop ha sido suspendido temporalmente por incumplimiento "
            "en el pago de las cuotas de financiamiento con indatech."
        )
        sub_lbl.setWordWrap(True)
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_lbl.setStyleSheet("color: #526B70; font-size: 14px;")
        c_layout.addWidget(sub_lbl)

        # Datos del titular (Nombre y Cédula)
        info_frame = QFrame()
        info_frame.setStyleSheet(
            "background-color: #F3F8F7; border: 1.5px solid #CBE0DC; border-radius: 12px; padding: 14px;"
        )
        info_layout = QVBoxLayout(info_frame)
        self.client_name_lbl = QLabel()
        self.client_name_lbl.setStyleSheet("font-size: 16.5px; font-weight: 900; color: #071D20;")
        self.client_cedula_lbl = QLabel()
        self.client_cedula_lbl.setStyleSheet("font-size: 15px; font-weight: 800; color: #008F64;")
        self.device_code_lbl = QLabel()
        self.device_code_lbl.setStyleSheet("font-size: 12.5px; color: #526B70; font-weight: 600;")
        info_layout.addWidget(self.client_name_lbl)
        info_layout.addWidget(self.client_cedula_lbl)
        info_layout.addWidget(self.device_code_lbl)
        c_layout.addWidget(info_frame)

        # Motivo específico del bloqueo / cuota vencida
        self.reason_lbl = QLabel()
        self.reason_lbl.setWordWrap(True)
        self.reason_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reason_lbl.setStyleSheet(
            "background-color: #FFF5F5; color: #C92A2A; border: 1.5px solid #FECACA; "
            "border-radius: 10px; padding: 13px; font-size: 14px; font-weight: 800;"
        )
        c_layout.addWidget(self.reason_lbl)

        # Opción 1: Verificar con el servidor online
        sync_btn = QPushButton("↻ Ya realicé mi pago — Verificar con el Servidor Ahora")
        sync_btn.setObjectName("primaryBtn")
        sync_btn.setMinimumHeight(44)
        sync_btn.clicked.connect(self._on_verify_online)
        c_layout.addWidget(sync_btn)

        # Opción 2: Desbloqueo sin internet mediante PIN firmado
        pin_title = QLabel("¿Sin conexión a Wi-Fi? Ingrese el PIN de Desbloqueo proporcionado por Indatech:")
        pin_title.setStyleSheet("font-size: 12.5px; font-weight: 800; color: #526B70; margin-top: 6px;")
        c_layout.addWidget(pin_title)

        pin_row = QHBoxLayout()
        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText("Formato: DD-XXXXXX (ej: 30-482910)")
        self.pin_input.setMinimumHeight(40)
        pin_btn = QPushButton("🔑 Desbloquear con PIN")
        pin_btn.setObjectName("successBtn")
        pin_btn.setMinimumHeight(40)
        pin_btn.clicked.connect(self._on_verify_pin)
        pin_row.addWidget(self.pin_input, 1)
        pin_row.addWidget(pin_btn)
        c_layout.addLayout(pin_row)

        self.feedback_lbl = QLabel("")
        self.feedback_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_lbl.setStyleSheet("font-size: 12.5px; font-weight: 700; color: #526B70;")
        c_layout.addWidget(self.feedback_lbl)

        center_row.addWidget(card)
        center_row.addStretch(1)
        root_layout.addLayout(center_row)
        root_layout.addStretch(1)

        self.refresh_lock_info()

    def refresh_lock_info(self) -> None:
        st = self.state_mgr.state
        policy = self.state_mgr.evaluate_current_policy()
        self.client_name_lbl.setText(f"Titular del Crédito: {st.get('client_name', 'N/A')}")
        self.client_cedula_lbl.setText(f"Número de Cédula: {st.get('client_cedula', 'N/A')}")
        self.device_code_lbl.setText(
            f"Equipo: {st.get('laptop_model', 'Laptop')}  |  "
            f"Código Creditech: {st.get('enrollment_code', 'N/A')}"
        )
        self.reason_lbl.setText(
            policy.get("lock_reason")
            or "Cuota vencida pendiente de pago. Comuníquese con Indatech / Creditech."
        )

    def show_full_lock(self) -> None:
        self._allow_close = False
        self.refresh_lock_info()
        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def unlock_and_close(self) -> None:
        self._allow_close = True
        self.hide()

    def _on_verify_online(self) -> None:
        self.feedback_lbl.setText("Consultando con el servidor central Creditech...")
        QApplication.processEvents()
        ok, msg = self.state_mgr.sync_with_server()
        policy = self.state_mgr.evaluate_current_policy()
        if not policy["locked"]:
            self.feedback_lbl.setStyleSheet("color: #00B580; font-weight: 800;")
            self.feedback_lbl.setText("¡Pago confirmado! Desbloqueando equipo...")
            self.unlock_and_close()
            self.on_unlocked_callback()
        else:
            self.refresh_lock_info()
            self.feedback_lbl.setStyleSheet("color: #E03131; font-weight: 800;")
            self.feedback_lbl.setText(
                f"El equipo continúa bloqueado en el servidor ({msg})"
            )

    def _on_verify_pin(self) -> None:
        pin = self.pin_input.text().strip()
        if not pin:
            self.feedback_lbl.setStyleSheet("color: #E03131; font-weight: 800;")
            self.feedback_lbl.setText("Ingrese un código PIN de desbloqueo.")
            return

        res = self.state_mgr.apply_offline_pin(pin)
        if res["valid"]:
            self.pin_input.clear()
            self.feedback_lbl.setStyleSheet("color: #00B580; font-weight: 800;")
            self.feedback_lbl.setText("¡PIN válido! Equipo desbloqueado.")
            self.unlock_and_close()
            self.on_unlocked_callback()
        else:
            self.feedback_lbl.setStyleSheet("color: #E03131; font-weight: 800;")
            self.feedback_lbl.setText(res["reason"])

    def closeEvent(self, event: QCloseEvent) -> None:
        if not self._allow_close:
            event.ignore()
        else:
            event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
            return
        super().keyPressEvent(event)


class ClientPortalWindow(QMainWindow):
    """Ventana principal moderna de Creditech by indatech. en la laptop del cliente."""

    def __init__(self, state_mgr: AgentStateManager) -> None:
        super().__init__()
        self.state_mgr = state_mgr
        self.setWindowTitle("Creditech by indatech. — Estado de Financiamiento del Equipo")
        self.setWindowIcon(QIcon(render_indatech_logo_pixmap(64, show_text=False)))
        self.setMinimumSize(900, 620)
        self.setStyleSheet(CREDITECH_QSS)

        self.lock_window = FullScreenLockWindow(
            state_mgr=self.state_mgr,
            on_unlocked_callback=self.refresh_ui,
        )

        self._build_ui()

        self.sync_timer = QTimer(self)
        self.sync_timer.setInterval(10_000)
        self.sync_timer.timeout.connect(self.periodic_check)
        self.sync_timer.start()

        self.refresh_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 22, 24, 22)
        main_layout.setSpacing(16)

        # Cabecera Creditech by indatech.
        header = QFrame()
        header.setObjectName("headerBanner")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 16, 20, 16)
        h_layout.setSpacing(16)

        h_layout.addWidget(IndatechLogoWidget(size=66, show_text=True))

        title_col = QVBoxLayout()
        brand_row = QHBoxLayout()
        brand = QLabel("CREDITECH")
        brand.setObjectName("brandTitle")
        pill = QLabel("by indatech.")
        pill.setObjectName("brandPill")
        brand_row.addWidget(brand)
        brand_row.addWidget(pill)
        brand_row.addStretch()

        sub = QLabel("Sistema de Control de Financiamiento, Avisos de Pago y Estado del Equipo")
        sub.setObjectName("brandSub")
        title_col.addLayout(brand_row)
        title_col.addWidget(sub)
        h_layout.addLayout(title_col, 1)

        self.sync_btn = QPushButton("↻ Sincronizar con Servidor")
        self.sync_btn.setObjectName("primaryBtn")
        self.sync_btn.clicked.connect(self.manual_sync)
        h_layout.addWidget(self.sync_btn)
        main_layout.addWidget(header)

        # Banner de Aviso de Pago (visible 1 día antes del vencimiento)
        self.warning_frame = QFrame()
        self.warning_frame.setObjectName("warningBanner")
        w_layout = QVBoxLayout(self.warning_frame)
        w_layout.setContentsMargins(18, 14, 18, 14)
        self.warning_label = QLabel()
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet("color: #92400E; font-weight: 800; font-size: 13.5px;")
        w_layout.addWidget(self.warning_label)
        self.warning_frame.setVisible(False)
        main_layout.addWidget(self.warning_frame)

        # Tarjeta con Nombre y Número de Cédula del cliente + Estado del equipo
        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QHBoxLayout(info_card)
        info_layout.setContentsMargins(22, 18, 22, 18)

        left_col = QVBoxLayout()
        self.client_name_lbl = QLabel()
        self.client_name_lbl.setObjectName("clientInfoTitle")
        self.client_cedula_lbl = QLabel()
        self.client_cedula_lbl.setStyleSheet("font-size: 14.5px; font-weight: 800; color: #008F64;")
        self.laptop_info_lbl = QLabel()
        self.laptop_info_lbl.setStyleSheet("font-size: 12.5px; color: #526B70; font-weight: 600;")
        left_col.addWidget(self.client_name_lbl)
        left_col.addWidget(self.client_cedula_lbl)
        left_col.addWidget(self.laptop_info_lbl)
        info_layout.addLayout(left_col, 1)

        right_col = QVBoxLayout()
        right_col.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.status_badge_lbl = QLabel()
        self.status_badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_due_lbl = QLabel()
        self.next_due_lbl.setStyleSheet("font-size: 12.5px; color: #526B70; font-weight: 700;")
        right_col.addWidget(self.status_badge_lbl)
        right_col.addWidget(self.next_due_lbl)
        info_layout.addLayout(right_col)

        main_layout.addWidget(info_card)

        # Tabla de Cuotas
        table_card = QFrame()
        table_card.setObjectName("card")
        t_layout = QVBoxLayout(table_card)
        t_layout.setContentsMargins(22, 18, 22, 18)

        t_title = QLabel("Cronograma de Cuotas del Financiamiento")
        t_title.setObjectName("sectionTitle")
        t_layout.addWidget(t_title)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Nº Cuota", "Fecha de Vencimiento", "Monto (USD)", "Estado"]
        )
        header_view = self.table.horizontalHeader()
        if header_view:
            header_view.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t_layout.addWidget(self.table)

        self.footer_sync_lbl = QLabel("Última sincronización: --")
        self.footer_sync_lbl.setStyleSheet("font-size: 12px; color: #526B70; font-weight: 600;")
        t_layout.addWidget(self.footer_sync_lbl)

        main_layout.addWidget(table_card, 1)

    def refresh_ui(self) -> None:
        st = self.state_mgr.state
        policy = self.state_mgr.evaluate_current_policy()

        self.client_name_lbl.setText(f"Cliente: {st.get('client_name', 'Sin registrar')}")
        self.client_cedula_lbl.setText(f"Número de Cédula: {st.get('client_cedula', 'N/A')}")
        self.laptop_info_lbl.setText(
            f"Equipo: {st.get('laptop_model', 'Laptop')}  |  "
            f"Serial: {st.get('laptop_serial') or 'N/A'}  |  "
            f"Código Creditech: {st.get('enrollment_code', 'N/A')}"
        )

        if policy["locked"]:
            self.status_badge_lbl.setText("🔒 EQUIPO BLOQUEADO")
            self.status_badge_lbl.setStyleSheet(
                "background-color: #FFF5F5; color: #E03131; border: 1.5px solid #FECACA; "
                "border-radius: 999px; padding: 7px 16px; font-weight: 900;"
            )
        elif policy["warning_due_soon"]:
            self.status_badge_lbl.setText("⚠️ AVISO DE PAGO (1 DÍA ANTES)")
            self.status_badge_lbl.setStyleSheet(
                "background-color: #FFFBEB; color: #D97706; border: 1.5px solid #FDE68A; "
                "border-radius: 999px; padding: 7px 16px; font-weight: 900;"
            )
        else:
            self.status_badge_lbl.setText("✓ EQUIPO ACTIVO Y AL DÍA")
            self.status_badge_lbl.setStyleSheet(
                "background-color: #E6FBF4; color: #008F64; border: 1.5px solid #99F3D6; "
                "border-radius: 999px; padding: 7px 16px; font-weight: 900;"
            )

        if policy["next_installment"]:
            ni = policy["next_installment"]
            self.next_due_lbl.setText(
                f"Próxima cuota: #{ni['number']} (${ni['amount']:.2f}) vence el {ni['due_date']}"
            )
        else:
            self.next_due_lbl.setText("Todas las cuotas han sido pagadas.")

        if policy["warning_due_soon"] and not policy["locked"]:
            self.warning_frame.setVisible(True)
            self.warning_label.setText(policy["warning_message"])
        else:
            self.warning_frame.setVisible(False)

        installments = st.get("installments", [])
        self.table.setRowCount(len(installments))
        today_iso = date.today().isoformat()
        for row_idx, inst in enumerate(installments):
            num_item = QTableWidgetItem(f"Cuota #{inst.get('number', row_idx + 1)}")
            due_str = str(inst.get("due_date", ""))
            due_item = QTableWidgetItem(due_str)
            amt_item = QTableWidgetItem(f"${float(inst.get('amount', 0.0)):.2f}")

            is_paid = inst.get("status") == "paid"
            if is_paid:
                status_text = "✓ PAGADA"
            elif due_str < today_iso:
                status_text = "🔒 VENCIDA (EN MORA)"
            else:
                status_text = "⏳ PENDIENTE"
            st_item = QTableWidgetItem(status_text)

            self.table.setItem(row_idx, 0, num_item)
            self.table.setItem(row_idx, 1, due_item)
            self.table.setItem(row_idx, 2, amt_item)
            self.table.setItem(row_idx, 3, st_item)

        self.footer_sync_lbl.setText(
            f"Última sincronización con servidor ({st.get('server_url')}): "
            f"{st.get('last_sync_at') or 'Pendiente'}"
        )

    def manual_sync(self) -> None:
        self.periodic_check(show_feedback=True)

    def periodic_check(self, show_feedback: bool = False) -> None:
        ok, msg = self.state_mgr.sync_with_server()
        self.refresh_ui()
        policy = self.state_mgr.evaluate_current_policy()

        if policy["locked"]:
            if not self.lock_window.isVisible():
                self.lock_window.show_full_lock()
            else:
                self.lock_window.refresh_lock_info()
            return
        else:
            if self.lock_window.isVisible():
                self.lock_window.unlock_and_close()

        today_iso = date.today().isoformat()
        if (
            policy["warning_due_soon"]
            and self.state_mgr.state.get("last_warning_shown_date") != today_iso
        ):
            self.state_mgr.state["last_warning_shown_date"] = today_iso
            self.state_mgr.save()
            dlg = PaymentReminderDialog(
                client_name=self.state_mgr.state.get("client_name", ""),
                client_cedula=self.state_mgr.state.get("client_cedula", ""),
                warning_message=policy["warning_message"],
                next_installment=policy["next_installment"],
                parent=self,
            )
            dlg.exec()

        if show_feedback:
            QMessageBox.information(self, "Creditech by indatech.", msg)
