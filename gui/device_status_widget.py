# -*- coding: utf-8 -*-
"""
Bandeau de statut permanent haute visibilité pour Optima MTK Tool.
Format compact (38px), sans conteneur bloquant, avec affichage horizontal clair :
  - 🔴 "Aucun appareil connecté" (LED clignotante)
  - 🟢 "Connecté : [Modèle] [Mode BROM - Port]"
  - 🟡 "Connecté : Appareil branché [Mode Normal]"
"""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont

COLOR_BG_PANEL     = "#111522"
COLOR_TEXT_PRIMARY = "#ffffff"
COLOR_TEXT_MUTED   = "#94a3b8"
COLOR_BORDER       = "#232c40"
COLOR_SUCCESS      = "#10b981"
COLOR_WARNING      = "#f59e0b"
COLOR_ERROR        = "#ef4444"
COLOR_ERROR_DARK   = "#7f1d1d"
COLOR_CONNECTED_BG = "#081a10"
COLOR_WARNING_BG   = "#1f1807"


class DeviceStatusBanner(QFrame):
    """Bandeau de statut permanent en ligne unique (38px de haut, zéro blocage)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("permanentStatusBar")
        self.setFixedHeight(38)

        self._state = "NONE"
        self._led_bright = True

        self._build_ui()
        self._apply_style_none()

        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(850)
        self._blink_timer.timeout.connect(self._blink_led)
        self._blink_timer.start()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        # Indicateur LED
        self.lbl_led = QLabel("●")
        self.lbl_led.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.lbl_led.setFixedWidth(20)
        self.lbl_led.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_led)

        # Statut textuel principal
        self.lbl_status = QLabel("🔴 Aucun appareil connecté")
        self.lbl_status.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.lbl_status.setStyleSheet(f"color: {COLOR_ERROR};")
        layout.addWidget(self.lbl_status)

        # Séparateur / Détail
        self.lbl_detail = QLabel("— Surveillance USB continue active (BROM MediaTek, Fastboot, ADB)")
        self.lbl_detail.setFont(QFont("Segoe UI", 10))
        self.lbl_detail.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        layout.addWidget(self.lbl_detail)

        layout.addStretch()

        # Pill badge de mode
        self.lbl_pill = QLabel("VEILLE")
        self.lbl_pill.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.lbl_pill.setStyleSheet("""
            background-color: #241414;
            color: #ef4444;
            border: 1px solid #4a1f1f;
            border-radius: 4px;
            padding: 2px 10px;
        """)
        layout.addWidget(self.lbl_pill)

    @pyqtSlot(str, str, str, str)
    def update_status(self, mode_str: str, title: str, subtitle: str, color: str):
        is_none = (mode_str == "NONE")
        is_warning = (mode_str in ("USB_NORMAL", "NORMAL"))

        if is_none:
            self._state = "NONE"
            self.lbl_status.setText("🔴 Aucun appareil connecté")
            self.lbl_detail.setText("— Surveillance USB active (BROM, Fastboot, ADB)")
            self.lbl_pill.setText("VEILLE")
            self.lbl_pill.setStyleSheet("background-color: #241414; color: #ef4444; border: 1px solid #4a1f1f; border-radius: 4px; padding: 2px 10px;")
            self._apply_style_none()
            if not self._blink_timer.isActive():
                self._blink_timer.start()

        elif is_warning:
            self._state = "WARNING"
            self._blink_timer.stop()
            display_title = title if title.startswith("🟡") else f"🟡 {title}"
            self.lbl_status.setText(display_title)
            self.lbl_detail.setText(f"— {subtitle or 'Débogage USB inactif. Éteignez pour passer en mode BROM.'}")
            self.lbl_pill.setText("NORMAL")
            self.lbl_pill.setStyleSheet("background-color: #2d2610; color: #f59e0b; border: 1px solid #5a4b18; border-radius: 4px; padding: 2px 10px;")
            self._apply_style_warning()

        else:
            self._state = "CONNECTED"
            self._blink_timer.stop()
            display_title = title if title.startswith("🟢") else f"🟢 {title}"
            self.lbl_status.setText(display_title)
            self.lbl_detail.setText(f"— {subtitle or 'Liaison prête'}")
            pill_text = mode_str
            if mode_str == "ADB":
                pill_text = "ADB ACTIVE"
            elif mode_str == "BROM":
                pill_text = "BROM / VCOM"
            elif mode_str == "FASTBOOT":
                pill_text = "FASTBOOT"
            self.lbl_pill.setText(pill_text)
            self.lbl_pill.setStyleSheet("background-color: #0d2818; color: #10b981; border: 1px solid #1e5a35; border-radius: 4px; padding: 2px 10px;")
            self._apply_style_connected()

    def set_device_info(self, model_name: str, mode_name: str, port_name: str = ""):
        self._state = "CONNECTED"
        self._blink_timer.stop()
        loc = f" - {port_name}" if port_name else ""
        self.lbl_status.setText(f"🟢 Connecté : {model_name} [Mode {mode_name}{loc}]")
        self.lbl_detail.setText("— Synchronisation matérielle active")
        self.lbl_pill.setText(f"{mode_name.upper()}")
        self.lbl_pill.setStyleSheet("background-color: #0d2818; color: #10b981; border: 1px solid #1e5a35; border-radius: 4px; padding: 2px 10px;")
        self._apply_style_connected()

    def _blink_led(self):
        if self._state != "NONE":
            self._blink_timer.stop()
            return
        color = COLOR_ERROR if self._led_bright else COLOR_ERROR_DARK
        self.lbl_led.setStyleSheet(f"color: {color};")
        self._led_bright = not self._led_bright

    def _apply_style_none(self):
        self.lbl_led.setStyleSheet(f"color: {COLOR_ERROR};")
        self.lbl_status.setStyleSheet(f"color: {COLOR_ERROR}; font-weight: bold;")
        self.setStyleSheet(f"""
            QFrame#permanentStatusBar {{
                background-color: {COLOR_BG_PANEL};
                border-bottom: 1px solid {COLOR_ERROR}66;
            }}
        """)

    def _apply_style_connected(self):
        self.lbl_led.setStyleSheet(f"color: {COLOR_SUCCESS};")
        self.lbl_status.setStyleSheet(f"color: {COLOR_SUCCESS}; font-weight: bold;")
        self.setStyleSheet(f"""
            QFrame#permanentStatusBar {{
                background-color: {COLOR_CONNECTED_BG};
                border-bottom: 1px solid {COLOR_SUCCESS}77;
            }}
        """)

    def _apply_style_warning(self):
        self.lbl_led.setStyleSheet(f"color: {COLOR_WARNING};")
        self.lbl_status.setStyleSheet(f"color: {COLOR_WARNING}; font-weight: bold;")
        self.setStyleSheet(f"""
            QFrame#permanentStatusBar {{
                background-color: {COLOR_WARNING_BG};
                border-bottom: 1px solid {COLOR_WARNING}66;
            }}
        """)
