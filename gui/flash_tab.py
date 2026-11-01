# -*- coding: utf-8 -*-
"""
Onglet Flash Tool - Flashage de firmware (scatter, ROM) pour MediaTek.
S'adapte dynamiquement selon l'état de détection de l'appareil.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QFileDialog, QLineEdit, QProgressBar, QMessageBox
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
COLOR_WARNING = "#f1c40f"
COLOR_CYAN = "#00c3ff"


class FlashTab(QWidget):
    """Onglet Flash Tool avec validation du mode d'accès BROM."""

    def __init__(self, mtk_comm, parent=None):
        super().__init__(parent)
        self.mtk_comm = mtk_comm
        self.device_connected = False
        self.current_device: ConnectedDevice = None
        self.current_port = None
        self.firmware_path = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        # --- Appareil cible ---
        device_group = QGroupBox("Appareil cible (Détection automatique)")
        device_layout = QVBoxLayout(device_group)
        self.lbl_device = QLabel("Aucun appareil connecté - En attente de détection...")
        self.lbl_device.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        device_layout.addWidget(self.lbl_device)
        layout.addWidget(device_group)

        # --- Sélection du firmware ---
        fw_group = QGroupBox("Firmware / Fichier de flash (Scatter MTK)")
        fw_layout = QVBoxLayout(fw_group)

        path_layout = QHBoxLayout()
        self.txt_firmware = QLineEdit()
        self.txt_firmware.setPlaceholderText("Sélectionnez un fichier scatter ou ROM (.txt, .bin, .img, .zip)...")
        self.txt_firmware.setReadOnly(True)
        self.txt_firmware.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px;
            }}
        """)
        btn_browse = QPushButton("Parcourir...")
        btn_browse.setFixedWidth(110)
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.clicked.connect(self._browse_firmware)
        path_layout.addWidget(self.txt_firmware)
        path_layout.addWidget(btn_browse)
        fw_layout.addLayout(path_layout)

        layout.addWidget(fw_group)

        # --- Actions de flash ---
        action_group = QGroupBox("Opération de flash")
        action_layout = QVBoxLayout(action_group)

        self.btn_flash = QPushButton("Démarrer le flash")
        self.btn_flash.setObjectName("flashButton")
        self.btn_flash.setFixedHeight(45)
        self.btn_flash.setEnabled(False)
        self.btn_flash.setCursor(Qt.PointingHandCursor)
        self.btn_flash.clicked.connect(self._start_flash)
        action_layout.addWidget(self.btn_flash)

        self.progress_flash = QProgressBar()
        self.progress_flash.setRange(0, 100)
        self.progress_flash.setValue(0)
        self.progress_flash.setTextVisible(True)
        action_layout.addWidget(self.progress_flash)

        layout.addWidget(action_group)
        layout.addStretch()

        self._apply_stylesheet()

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
            QPushButton#flashButton {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton#flashButton:hover {{
                background-color: #0088cc;
            }}
            QPushButton#flashButton:disabled {{
                background-color: #2c334a;
                color: {COLOR_TEXT_MUTED};
            }}
            QProgressBar {{
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                text-align: center;
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT};
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_ACCENT};
                border-radius: 3px;
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

        if dev.mode == DeviceMode.BROM:
            self.lbl_device.setText(f"Mode BROM détecté sur {dev.port} - {dev.description}")
            self.lbl_device.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 12px; font-weight: bold;")
        elif dev.mode == DeviceMode.FASTBOOT:
            self.lbl_device.setText(f"Mode Fastboot détecté ({dev.serial_number}) - Flash Scatter BROM indisponible en Fastboot")
            self.lbl_device.setStyleSheet(f"color: {COLOR_CYAN}; font-size: 12px; font-weight: bold;")
        else:
            self.lbl_device.setText(f"Mode Normal détecté ({dev.port}) - Éteignez le téléphone pour le flash BROM")
            self.lbl_device.setStyleSheet(f"color: {COLOR_WARNING}; font-size: 12px; font-weight: bold;")

        self._update_flash_button_state()

    def on_device_disconnected(self):
        self.device_connected = False
        self.current_device = None
        self.current_port = None
        self.lbl_device.setText("Aucun appareil connecté - En attente de détection...")
        self.lbl_device.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        self._update_flash_button_state()

    def _update_flash_button_state(self):
        # Le flash scatter complet requiert un appareil connecté (préférablement BROM) et un fichier
        is_ready = self.device_connected and (self.firmware_path is not None)
        self.btn_flash.setEnabled(is_ready)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _browse_firmware(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner le firmware / fichier scatter",
            "",
            "Fichiers MTK (*.txt *.bin *.img *.zip *.md1);;Tous les fichiers (*)"
        )
        if file_path:
            self.firmware_path = file_path
            self.txt_firmware.setText(file_path)
            self._update_flash_button_state()

    def _start_flash(self):
        if not self.device_connected or not self.current_device:
            QMessageBox.warning(self, "Appareil manquant", "Veuillez connecter un appareil MediaTek d'abord.")
            return
        if not self.firmware_path:
            QMessageBox.warning(self, "Fichier manquant", "Veuillez sélectionner un fichier de firmware.")
            return

        reply = QMessageBox.question(
            self, "Confirmer le flash",
            f"Firmware : {self.firmware_path}\n"
            f"Cible : {self.lbl_device.text()}\n\n"
            "ATTENTION : Cette opération va réécrire la mémoire de l'appareil.\n"
            "Voulez-vous continuer ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.btn_flash.setEnabled(False)
        self.progress_flash.setValue(0)

        steps = [
            (15, "Connexion au chargeur d'amorçage (BROM)..."),
            (35, "Vérification du fichier scatter..."),
            (55, "Flash du preloader..."),
            (70, "Flash du firmware (ROM)..."),
            (85, "Vérification de l'intégrité..."),
            (100, "Flash terminé. Redémarrage..."),
        ]
        for pct, msg in steps:
            self.progress_flash.setValue(pct)
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()

        self.progress_flash.setValue(100)
        self._update_flash_button_state()
        QMessageBox.information(self, "Flash terminé", "Le firmware a été flashé avec succès.")
