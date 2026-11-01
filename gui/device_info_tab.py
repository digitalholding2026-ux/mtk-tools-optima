# -*- coding: utf-8 -*-
"""
Onglet Informations Appareil - Affichage des détails du périphérique MediaTek connecté.
S'actualise automatiquement lors de la détection d'un appareil (BROM, Fastboot, Normal/AT).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QGridLayout, QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.detector import ConnectedDevice, DeviceMode

COLOR_BG_TAB = "#1e2332"
COLOR_BG_PANEL = "#161a28"
COLOR_ACCENT = "#00a2ff"
COLOR_TEXT = "#e8eaf2"
COLOR_TEXT_MUTED = "#8a92a8"
COLOR_BORDER = "#2c334a"
COLOR_SUCCESS = "#2ecc71"
COLOR_CYAN = "#00c3ff"
COLOR_WARNING = "#f1c40f"


class DeviceInfoTab(QWidget):
    """Onglet Informations Appareil avec actualisation automatique."""

    def __init__(self, mtk_comm, parent=None):
        super().__init__(parent)
        self.mtk_comm = mtk_comm
        self.device_connected = False
        self.current_device: ConnectedDevice = None
        self.current_port = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        # --- Informations appareil ---
        info_group = QGroupBox("Informations du périphérique connecté")
        info_layout = QGridLayout(info_group)
        info_layout.setHorizontalSpacing(20)
        info_layout.setVerticalSpacing(12)

        self.lbl_mode = self._create_info_row(info_layout, 0, 0, "Mode détecté :", "En attente")
        self.lbl_port = self._create_info_row(info_layout, 0, 1, "Port / Liaison :", "—")
        self.lbl_model = self._create_info_row(info_layout, 1, 0, "Nom / Modèle :", "—")
        self.lbl_chip = self._create_info_row(info_layout, 1, 1, "Chipset / Processeur :", "—")
        self.lbl_android = self._create_info_row(info_layout, 2, 0, "Version Android :", "—")
        self.lbl_imei = self._create_info_row(info_layout, 2, 1, "IMEI / N° Série :", "—")
        self.lbl_proto = self._create_info_row(info_layout, 3, 0, "Protocole :", "—")
        self.lbl_ident = self._create_info_row(info_layout, 3, 1, "ID Matériel / VID:PID :", "—")

        layout.addWidget(info_group)

        # --- Détails techniques ---
        detail_group = QGroupBox("Journal des spécifications matérielles")
        detail_layout = QVBoxLayout(detail_group)
        self.txt_details = QTextEdit()
        self.txt_details.setReadOnly(True)
        self.txt_details.setMaximumHeight(180)
        self.txt_details.setPlaceholderText("Aucune information disponible. Branchez un appareil pour afficher les spécifications détectées en direct.")
        self.txt_details.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 11px;
                padding: 8px;
            }}
        """)
        detail_layout.addWidget(self.txt_details)
        layout.addWidget(detail_group)

        # --- Boutons d'action ---
        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("📋 Lire les informations appareil")
        self.btn_refresh.setFixedHeight(38)
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(self._on_read_info_clicked)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()
        self._apply_stylesheet()

    def _create_info_row(self, layout, row, col, label_text, default_value):
        lbl_label = QLabel(label_text)
        lbl_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        lbl_value = QLabel(default_value)
        lbl_value.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: bold;")
        layout.addWidget(lbl_label, row, col * 2)
        layout.addWidget(lbl_value, row, col * 2 + 1)
        return lbl_value

    def _apply_stylesheet(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_BG_TAB};
                color: {COLOR_TEXT};
            }}
            QGroupBox {{
                background-color: {COLOR_BG_PANEL};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                margin-top: 15px;
                font-weight: bold;
                color: {COLOR_TEXT};
                padding: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: {COLOR_ACCENT};
            }}
            QPushButton {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: {COLOR_ACCENT};
                background-color: #242a3c;
            }}
        """)

    # ------------------------------------------------------------------
    # Callbacks de connexion
    # ------------------------------------------------------------------
    def on_device_connected(self, device_or_port, info=None):
        if isinstance(device_or_port, ConnectedDevice):
            dev = device_or_port
        else:
            dev = ConnectedDevice(
                mode=DeviceMode.BROM,
                identifier=str(device_or_port),
                port=str(device_or_port),
                description=str(info or "")
            )

        self.device_connected = True
        self.current_device = dev
        self.current_port = dev.port or dev.identifier

        self._refresh_info()

    def on_device_disconnected(self):
        self.device_connected = False
        self.current_device = None
        self.current_port = None

        self.lbl_mode.setText("En attente")
        self.lbl_mode.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; font-weight: bold;")

        for lbl in [self.lbl_port, self.lbl_model, self.lbl_chip, self.lbl_android, self.lbl_imei, self.lbl_proto, self.lbl_ident]:
            lbl.setText("—")
            lbl.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: bold;")

        self.txt_details.clear()
        self.txt_details.setPlaceholderText("Aucune information disponible. Branchez un appareil pour afficher les spécifications détectées en direct.")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _on_read_info_clicked(self):
        """Déclenche la lecture des infos via l'assistant de connexion si nécessaire."""
        main_win = self.window()
        if hasattr(main_win, "run_action_with_assistant"):
            main_win.run_action_with_assistant(
                action_name="Lire Infos",
                operation_func=self._execute_read_info_with_device,
                target_modes=[DeviceMode.BROM, DeviceMode.FASTBOOT, DeviceMode.NORMAL]
            )
        else:
            self._refresh_info()

    def _execute_read_info_with_device(self, device: ConnectedDevice):
        """Appelé lorsque l'appareil est détecté par l'assistant."""
        self.device_connected = True
        self.current_device = device
        self.current_port = device.port or device.identifier
        self._refresh_info()

    def _refresh_info(self):
        if not self.device_connected or not self.current_device:
            return

        dev = self.current_device
        raw_info = self.mtk_comm.read_device_info()

        # Mode et couleur
        self.lbl_mode.setText(dev.mode_display)
        self.lbl_mode.setStyleSheet(f"color: {dev.color}; font-size: 12px; font-weight: bold;")

        # Port / Identifiant
        loc = dev.port or dev.serial_number or dev.identifier
        self.lbl_port.setText(loc)

        # Modèle & Chip
        self.lbl_model.setText(raw_info.get("model", dev.description))
        self.lbl_chip.setText(raw_info.get("chip", "MediaTek MTK"))
        self.lbl_android.setText(raw_info.get("android", "—"))
        self.lbl_imei.setText(raw_info.get("imei", raw_info.get("serial", "—")))

        # Protocole & Identifiant
        self.lbl_proto.setText(dev.protocol or raw_info.get("protocol", "—"))
        if dev.vid and dev.pid:
            self.lbl_ident.setText(f"VID: 0x{dev.vid:04X} | PID: 0x{dev.pid:04X}")
        elif dev.serial_number:
            self.lbl_ident.setText(f"Série : {dev.serial_number}")
        else:
            self.lbl_ident.setText(dev.identifier)

        # Détails techniques textuels
        self.txt_details.clear()
        self.txt_details.append(f"=== RAPPORT D'IDENTIFICATION MATÉRIELLE ===")
        self.txt_details.append(f"• Mode de fonctionnement : {dev.mode_display} ({dev.mode.value})")
        self.txt_details.append(f"• Identifiant système     : {dev.identifier}")
        if dev.port:
            self.txt_details.append(f"• Port de communication   : {dev.port}")
        if dev.serial_number:
            self.txt_details.append(f"• Numéro de série USB     : {dev.serial_number}")
        if dev.vid and dev.pid:
            self.txt_details.append(f"• Identifiants USB        : VID=0x{dev.vid:04X}, PID=0x{dev.pid:04X}")
        if dev.manufacturer:
            self.txt_details.append(f"• Fabricant               : {dev.manufacturer}")
        if dev.protocol:
            self.txt_details.append(f"• Protocole actif         : {dev.protocol}")
        self.txt_details.append(f"• Statut MTK Comm         : Connecté et synchronisé")
        self.txt_details.append("===========================================")
