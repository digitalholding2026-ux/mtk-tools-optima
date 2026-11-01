# -*- coding: utf-8 -*-
"""
Onglet Accueil (Dashboard) de l'application Optima MTK Tool.
Affiche l'état général de connexion et des raccourcis rapides.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QGroupBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont

COLOR_BG_TAB = "#1e2332"
COLOR_BG_PANEL = "#161a28"
COLOR_ACCENT = "#00a2ff"
COLOR_TEXT = "#e8eaf2"
COLOR_TEXT_MUTED = "#8a92a8"
COLOR_BORDER = "#2c334a"
COLOR_SUCCESS = "#2ecc71"
COLOR_WARNING = "#f1c40f"


class DashboardTab(QWidget):
    """Onglet Accueil avec état de connexion et actions rapides."""

    def __init__(self, com_detector, mtk_comm, parent=None):
        super().__init__(parent)
        self.com_detector = com_detector
        self.mtk_comm = mtk_comm
        self.device_connected = False
        self.current_port = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # --- Bloc d'état de connexion ---
        status_group = QGroupBox("État de la connexion")
        status_group.setObjectName("statusGroup")
        status_layout = QVBoxLayout(status_group)

        self.lbl_port = QLabel("Aucun port détecté")
        self.lbl_port.setObjectName("lblPort")
        self.lbl_port.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.lbl_port.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

        self.lbl_status = QLabel("Statut : Déconnecté")
        self.lbl_status.setObjectName("lblStatus")
        self.lbl_status.setFont(QFont("Segoe UI", 11))
        self.lbl_status.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

        status_layout.addWidget(self.lbl_port)
        status_layout.addWidget(self.lbl_status)
        layout.addWidget(status_group)

        # --- Actions rapides ---
        actions_group = QGroupBox("Actions rapides")
        actions_group.setObjectName("actionsGroup")
        actions_layout = QGridLayout(actions_group)
        actions_layout.setSpacing(15)

        btn_detect = QPushButton("Détecter l'appareil")
        btn_detect.setIcon(self.style().standardIcon(self.style().SP_MediaVolume))
        btn_detect.setFixedHeight(50)
        btn_detect.clicked.connect(self._detect_device)

        btn_frp = QPushButton("Accéder au déblocage FRP")
        btn_frp.setFixedHeight(50)
        btn_frp.clicked.connect(self._go_to_frp)

        btn_flash = QPushButton("Accéder à l'outil Flash")
        btn_flash.setFixedHeight(50)
        btn_flash.clicked.connect(self._go_to_flash)

        btn_info = QPushButton("Voir les informations appareil")
        btn_info.setFixedHeight(50)
        btn_info.clicked.connect(self._go_to_info)

        actions_layout.addWidget(btn_detect, 0, 0)
        actions_layout.addWidget(btn_frp, 0, 1)
        actions_layout.addWidget(btn_flash, 1, 0)
        actions_layout.addWidget(btn_info, 1, 1)

        layout.addWidget(actions_group)
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
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                border-color: {COLOR_ACCENT};
                background-color: #242a3c;
            }}
            QPushButton:pressed {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
            }}
        """)

    # ------------------------------------------------------------------
    # Slots / Callbacks
    # ------------------------------------------------------------------
    def on_device_connected(self, port, info):
        """Appelé quand un appareil est connecté."""
        self.device_connected = True
        self.current_port = port
        self.lbl_port.setText(f"Port : {port}")
        self.lbl_port.setStyleSheet(f"color: {COLOR_SUCCESS};")
        self.lbl_status.setText(f"Statut : Connecté - {info}")
        self.lbl_status.setStyleSheet(f"color: {COLOR_SUCCESS};")

    def on_device_disconnected(self):
        """Appelé quand l'appareil est déconnecté."""
        self.device_connected = False
        self.current_port = None
        self.lbl_port.setText("Aucun port détecté")
        self.lbl_port.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        self.lbl_status.setText("Statut : Déconnecté")
        self.lbl_status.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

    def _detect_device(self):
        from gui.main_window import MainWindow
        # Délègue à la fenêtre principale si besoin
        parent = self.window()
        if hasattr(parent, "_on_detect_clicked"):
            parent._on_detect_clicked()

    def _go_to_frp(self):
        tabs = self.window().tabs
        tabs.setCurrentIndex(1)

    def _go_to_flash(self):
        tabs = self.window().tabs
        tabs.setCurrentIndex(2)

    def _go_to_info(self):
        tabs = self.window().tabs
        tabs.setCurrentIndex(3)
