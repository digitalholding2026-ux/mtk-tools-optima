# -*- coding: utf-8 -*-
"""
Bandeau d'en-tête de statut permanent pour Optima MTK Tool.
Affiché en permanence en haut de l'interface principale :
  - 🔴 "Aucun appareil connecté"
  - 🟢 "Connecté : Infinix Hot 11 Play [Mode BROM]" (ou nom d'appareil détecté)
  - 🟢 "Connecté : Appareil Fastboot [Mode Fastboot]"
  - 🟢 "Connecté : Smartphone Android [Mode ADB (Débogage actif)]"
  - 🟡 "Connecté : Appareil branché (Mode Normal / Non sécurisé)"
"""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont

# Palette de couleurs Optima Telecom
COLOR_BG_PANEL     = "#131726"
COLOR_TEXT         = "#e8eaf2"
COLOR_TEXT_MUTED   = "#8a92a8"
COLOR_BORDER       = "#252c40"
COLOR_SUCCESS      = "#2ecc71"
COLOR_WARNING      = "#f1c40f"
COLOR_ERROR        = "#e74c3c"
COLOR_ERROR_DARK   = "#7f1f1f"
COLOR_CONNECTED_BG = "#0b1c11"
COLOR_WARNING_BG   = "#211b0e"
COLOR_ACCENT       = "#00a2ff"


class DeviceStatusBanner(QFrame):
    """
    Bandeau de statut permanent visible en permanence en haut de la fenêtre.
    Présente l'état en direct avec LED dynamique, nom du téléphone et mode d'accès.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("permanentStatusBar")
        self.setFixedHeight(54)

        self._state = "NONE"   # "NONE" | "CONNECTED" | "WARNING"
        self._led_bright = True

        self._build_ui()
        self._apply_style_none()

        # Animation de clignotement pour l'état déconnecté (veille)
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(850)
        self._blink_timer.timeout.connect(self._blink_led)
        self._blink_timer.start()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(14)

        # Indicateur LED
        self.lbl_led = QLabel("●")
        self.lbl_led.setObjectName("bannerLed")
        self.lbl_led.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.lbl_led.setFixedWidth(26)
        self.lbl_led.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_led)

        # Textes de statut (Titre formaté + Détail)
        text_container = QVBoxLayout()
        text_container.setContentsMargins(0, 0, 0, 0)
        text_container.setSpacing(2)

        self.lbl_status = QLabel("🔴 Aucun appareil connecté")
        self.lbl_status.setObjectName("bannerStatusTitle")
        self.lbl_status.setFont(QFont("Segoe UI", 12, QFont.Bold))

        self.lbl_detail = QLabel("Surveillance USB continue active (Modes : BROM MediaTek, Fastboot, ADB)...")
        self.lbl_detail.setObjectName("bannerStatusDetail")
        self.lbl_detail.setFont(QFont("Segoe UI", 9))

        text_container.addWidget(self.lbl_status)
        text_container.addWidget(self.lbl_detail)
        layout.addLayout(text_container)

        layout.addStretch()

        # Badge pill avec info protocole
        self.lbl_pill = QLabel("SURVEILLANCE ACTIVE")
        self.lbl_pill.setObjectName("statusPill")
        self.lbl_pill.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.lbl_pill.setStyleSheet("""
            QLabel#statusPill {
                background-color: #1a2034;
                color: #8a92a8;
                border: 1px solid #2c3550;
                border-radius: 12px;
                padding: 4px 12px;
                letter-spacing: 0.5px;
            }
        """)
        layout.addWidget(self.lbl_pill)

    @pyqtSlot(str, str, str, str)
    def update_status(self, mode_str: str, title: str, subtitle: str, color: str):
        """
        Met à jour l'affichage en temps réel.
        Format attendu :
          - Déconnecté : 🔴 "Aucun appareil connecté"
          - Connecté   : 🟢 "Connecté : [Nom de l'appareil] [Mode XXX]"
        """
        is_none = (mode_str == "NONE")
        is_warning = (mode_str == "USB_NORMAL")

        if is_none:
            self._state = "NONE"
            self.lbl_status.setText("🔴 Aucun appareil connecté")
            self.lbl_detail.setText(subtitle or "Surveillance USB active (Connectez un appareil en mode BROM, Fastboot ou ADB)")
            self.lbl_pill.setText("VEILLE")
            self.lbl_pill.setStyleSheet("background-color: #241414; color: #e74c3c; border: 1px solid #4a1f1f; border-radius: 12px; padding: 4px 12px;")
            self._apply_style_none()
            if not self._blink_timer.isActive():
                self._blink_timer.start()

        elif is_warning:
            self._state = "WARNING"
            self._blink_timer.stop()
            clean_title = title.replace("🟢", "").replace("🟡", "").replace("🔴", "").strip()
            self.lbl_status.setText(f"🟡 Connecté : Appareil branché [Mode Normal / Non sécurisé]")
            self.lbl_detail.setText(subtitle or "Débogage USB inactif. Pour FRP ou Flash, éteignez le smartphone et passez en mode BROM.")
            self.lbl_pill.setText("MODE NORMAL")
            self.lbl_pill.setStyleSheet("background-color: #2d2610; color: #f1c40f; border: 1px solid #5a4b18; border-radius: 12px; padding: 4px 12px;")
            self._apply_style_warning()

        else:
            self._state = "CONNECTED"
            self._blink_timer.stop()
            # Nettoyer titre des émojis dupliqués
            clean_title = title.replace("🟢", "").replace("🟡", "").replace("🔴", "").strip()
            # Construire libellé conforme à la spécification : 🟢 "Connecté : [Appareil] [Mode XXX]"
            if "mode BROM" in clean_title or mode_str == "BROM":
                formatted_title = f"🟢 Connecté : Périphérique MediaTek [Mode BROM / Preloader]"
            elif "Fastboot" in clean_title or mode_str == "FASTBOOT":
                formatted_title = f"🟢 Connecté : Smartphone Android [Mode Fastboot]"
            elif "ADB" in clean_title or mode_str == "ADB":
                formatted_title = f"🟢 Connecté : Smartphone Android [Mode ADB (Débogage actif)]"
            else:
                formatted_title = f"🟢 Connecté : {clean_title}"

            self.lbl_status.setText(formatted_title)
            self.lbl_detail.setText(subtitle or "Liaison prête pour les opérations de maintenance.")
            self.lbl_pill.setText(f"MODE {mode_str}")
            self.lbl_pill.setStyleSheet("background-color: #102d1b; color: #2ecc71; border: 1px solid #1e5a35; border-radius: 12px; padding: 4px 12px;")
            self._apply_style_connected()

    def set_device_info(self, model_name: str, mode_name: str, port_name: str = ""):
        """Permet de définir précisément le nom commercial du smartphone (ex: Infinix Hot 11 Play)."""
        self._state = "CONNECTED"
        self._blink_timer.stop()
        loc = f" - {port_name}" if port_name else ""
        self.lbl_status.setText(f"🟢 Connecté : {model_name} [Mode {mode_name}{loc}]")
        self.lbl_pill.setText(f"MODE {mode_name.upper()}")
        self._apply_style_connected()

    def _blink_led(self):
        """Animation de respiration LED pour l'état déconnecté."""
        if self._state != "NONE":
            self._blink_timer.stop()
            return
        color = COLOR_ERROR if self._led_bright else COLOR_ERROR_DARK
        self.lbl_led.setStyleSheet(f"color: {color};")
        self._led_bright = not self._led_bright

    def _apply_style_none(self):
        self.lbl_led.setStyleSheet(f"color: {COLOR_ERROR};")
        self.lbl_status.setStyleSheet(f"color: {COLOR_ERROR}; font-weight: bold; font-size: 12px;")
        self.lbl_detail.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px;")
        self.setStyleSheet(f"""
            QFrame#permanentStatusBar {{
                background-color: {COLOR_BG_PANEL};
                border-bottom: 2px solid {COLOR_ERROR}77;
            }}
        """)

    def _apply_style_connected(self):
        self.lbl_led.setStyleSheet(f"color: {COLOR_SUCCESS};")
        self.lbl_status.setStyleSheet(f"color: {COLOR_SUCCESS}; font-weight: bold; font-size: 12px;")
        self.lbl_detail.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px;")
        self.setStyleSheet(f"""
            QFrame#permanentStatusBar {{
                background-color: {COLOR_CONNECTED_BG};
                border-bottom: 2px solid {COLOR_SUCCESS}88;
            }}
        """)

    def _apply_style_warning(self):
        self.lbl_led.setStyleSheet(f"color: {COLOR_WARNING};")
        self.lbl_status.setStyleSheet(f"color: {COLOR_WARNING}; font-weight: bold; font-size: 12px;")
        self.lbl_detail.setStyleSheet(f"color: #d1b87a; font-size: 9px;")
        self.setStyleSheet(f"""
            QFrame#permanentStatusBar {{
                background-color: {COLOR_WARNING_BG};
                border-bottom: 2px solid {COLOR_WARNING}77;
            }}
        """)
