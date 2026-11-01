# -*- coding: utf-8 -*-
"""
Onglet Informations Appareil - Affichage des détails du périphérique MediaTek connecté.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QGridLayout, QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

COLOR_BG_TAB = "#1e2332"
COLOR_BG_PANEL = "#161a28"
COLOR_ACCENT = "#00a2ff"
COLOR_TEXT = "#e8eaf2"
COLOR_TEXT_MUTED = "#8a92a8"
COLOR_BORDER = "#2c334a"
COLOR_SUCCESS = "#2ecc71"


class DeviceInfoTab(QWidget):
    """Onglet Informations Appareil."""

    def __init__(self, mtk_comm, parent=None):
        super().__init__(parent)
        self.mtk_comm = mtk_comm
        self.device_connected = False
        self.current_port = None
        self.device_info = {}

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # --- Informations appareil ---
        info_group = QGroupBox("Informations du périphérique MediaTek")
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(10)

        self.lbl_port = self._create_info_row(info_layout, 0, 0, "Port COM :", "—")
        self.lbl_model = self._create_info_row(info_layout, 0, 1, "Modèle :", "—")
        self.lbl_chip = self._create_info_row(info_layout, 1, 0, "Processeur :", "—")
        self.lbl_android = self._create_info_row(info_layout, 1, 1, "Android :", "—")
        self.lbl_baseband = self._create_info_row(info_layout, 2, 0, "Baseband :", "—")
        self.lbl_imei = self._create_info_row(info_layout, 2, 1, "IMEI :", "—")

        layout.addWidget(info_group)

        # --- Détails techniques ---
        detail_group = QGroupBox("Détails techniques")
        detail_layout = VBoxLayout = QVBoxLayout(detail_group)
        self.txt_details = QTextEdit()
        self.txt_details.setReadOnly(True)
        self.txt_details.setMaximumHeight(160)
        self.txt_details.setPlaceholderText("Aucune information disponible. Connectez un appareil pour afficher les détails.")
        self.txt_details.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }}
        """)
        detail_layout.addWidget(self.txt_details)
        layout.addWidget(detail_group)

        # --- Boutons d'action ---
        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("Actualiser les informations")
        btn_refresh.setFixedHeight(36)
        btn_refresh.setCursor(Qt.PointingHandCursor)
        btn_refresh.clicked.connect(self._refresh_info)
        btn_layout.addWidget(btn_refresh)
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
                padding: 6px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                border-color: {COLOR_ACCENT};
                background-color: #242a3c;
            }}
        """)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------
    def on_device_connected(self, port, info):
        self.device_connected = True
        self.current_port = port
        self.lbl_port.setText(port)
        self.lbl_port.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 12px; font-weight: bold;")
        # Parsing simplifié de l'info (à affiner selon la réelle réponse MTK)
        parts = info.split("|")
        if len(parts) >= 1:
            self.lbl_model.setText(parts[0].strip())
        if len(parts) >= 2:
            self.lbl_chip.setText(parts[1].strip())
        self._refresh_info()

    def on_device_disconnected(self):
        self.device_connected = False
        self.current_port = None
        for lbl in [self.lbl_port, self.lbl_model, self.lbl_chip, self.lbl_android, self.lbl_baseband, self.lbl_imei]:
            lbl.setText("—")
            lbl.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: bold;")
        self.txt_details.clear()
        self.txt_details.setPlaceholderText("Aucune information disponible. Connectez un appareil pour afficher les détails.")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _refresh_info(self):
        if not self.device_connected:
            return
        self.txt_details.clear()
        self.txt_details.append(f"Port : {self.current_port}")
        self.txt_details.append(f"Modèle détecté : {self.lbl_model.text()}")
        self.txt_details.append(f"Processeur : {self.lbl_chip.text()}")
        self.txt_details.append(f"Statut : Connecté en mode BROM / préloader")
        self.txt_details.append("")
        self.txt_details.append("Détails techniques récupérés depuis l'appareil MediaTek.")
        self.txt_details.append("(À implémenter : lecture complète des propriétés via core/mtk_communication.py)")
