# -*- coding: utf-8 -*-
"""
Onglet Accueil (Dashboard) de l'application Optima MTK Tool.
Affiche l'état de détection automatique en temps réel et les raccourcis d'action.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QGroupBox
)
from PyQt5.QtCore import Qt, QSize
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
COLOR_PURPLE = "#a29bfe"


class DashboardTab(QWidget):
    """Onglet Accueil avec suivi dynamique des périphériques et actions rapides."""

    def __init__(self, detector, mtk_comm, parent=None):
        super().__init__(parent)
        self.detector = detector
        self.mtk_comm = mtk_comm
        self.device_connected = False
        self.current_device: ConnectedDevice = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        # --- Bloc d'état de détection automatique ---
        status_group = QGroupBox("Surveillance des périphériques (Temps Réel)")
        status_group.setObjectName("statusGroup")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(12)

        # Ligne 1 : Badge de mode et indicateur
        header_row = QHBoxLayout()
        self.badge_mode = QLabel("EN ATTENTE")
        self.badge_mode.setObjectName("badgeMode")
        self.badge_mode.setStyleSheet(self._badge_style("#8a92a8"))

        self.lbl_headline = QLabel("En attente de connexion d'un appareil...")
        self.lbl_headline.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.lbl_headline.setStyleSheet(f"color: {COLOR_TEXT};")

        header_row.addWidget(self.badge_mode)
        header_row.addWidget(self.lbl_headline)
        header_row.addStretch()
        status_layout.addLayout(header_row)

        # Ligne 2 : Détails techniques de connexion
        details_layout = QGridLayout()
        details_layout.setHorizontalSpacing(25)
        details_layout.setVerticalSpacing(6)

        self.lbl_port_label = QLabel("Port / Connexion :")
        self.lbl_port_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        self.lbl_port_value = QLabel("Aucun")
        self.lbl_port_value.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; font-weight: bold;")

        self.lbl_proto_label = QLabel("Protocole actif :")
        self.lbl_proto_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        self.lbl_proto_value = QLabel("Scan automatique actif (BROM / Fastboot / Normal)")
        self.lbl_proto_value.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")

        self.lbl_advice_label = QLabel("Recommandation :")
        self.lbl_advice_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        self.lbl_advice_value = QLabel("Connectez l'appareil éteint avec Volume- pour le mode BROM, ou allumez en mode Fastboot.")
        self.lbl_advice_value.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-style: italic;")

        details_layout.addWidget(self.lbl_port_label, 0, 0)
        details_layout.addWidget(self.lbl_port_value, 0, 1)
        details_layout.addWidget(self.lbl_proto_label, 1, 0)
        details_layout.addWidget(self.lbl_proto_value, 1, 1)
        details_layout.addWidget(self.lbl_advice_label, 2, 0)
        details_layout.addWidget(self.lbl_advice_value, 2, 1)

        status_layout.addLayout(details_layout)
        layout.addWidget(status_group)

        # --- Actions rapides ---
        actions_group = QGroupBox("Actions rapides avec Assistant Just-In-Time")
        actions_group.setObjectName("actionsGroup")
        actions_layout = QGridLayout(actions_group)
        actions_layout.setSpacing(15)

        self.btn_frp = QPushButton("🔒 Effacer FRP (Assistant JIT)")
        self.btn_frp.setFixedHeight(50)
        self.btn_frp.setCursor(Qt.PointingHandCursor)
        self.btn_frp.clicked.connect(self._launch_frp_action)

        self.btn_reset = QPushButton("🧹 Factory Reset (Assistant JIT)")
        self.btn_reset.setFixedHeight(50)
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.clicked.connect(self._launch_factory_reset_action)

        self.btn_flash = QPushButton("⚡ Outil Flash (Scatter MTK)")
        self.btn_flash.setFixedHeight(50)
        self.btn_flash.setCursor(Qt.PointingHandCursor)
        self.btn_flash.clicked.connect(self._go_to_flash)

        self.btn_info = QPushButton("📋 Lire Infos Appareil")
        self.btn_info.setFixedHeight(50)
        self.btn_info.setCursor(Qt.PointingHandCursor)
        self.btn_info.clicked.connect(self._launch_read_info_action)

        actions_layout.addWidget(self.btn_frp, 0, 0)
        actions_layout.addWidget(self.btn_reset, 0, 1)
        actions_layout.addWidget(self.btn_flash, 1, 0)
        actions_layout.addWidget(self.btn_info, 1, 1)

        layout.addWidget(actions_group)
        layout.addStretch()

        self._apply_stylesheet()

    def _badge_style(self, color_hex: str) -> str:
        """Génère le style CSS du badge de mode."""
        return f"""
            QLabel#badgeMode {{
                background-color: {color_hex}22;
                color: {color_hex};
                border: 1px solid {color_hex};
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
        """

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
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
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
    # Mises à jour dynamiques de connexion
    # ------------------------------------------------------------------
    def on_device_connected(self, device_or_port, info=None):
        """Appelé quand un appareil est détecté en arrière-plan."""
        if isinstance(device_or_port, ConnectedDevice):
            dev = device_or_port
        else:
            # Rétrocompatibilité si appelé avec des chaînes
            dev = ConnectedDevice(
                mode=DeviceMode.BROM,
                identifier=str(device_or_port),
                port=str(device_or_port),
                description=str(info or ""),
                protocol="MediaTek VCOM"
            )

        self.device_connected = True
        self.current_device = dev

        # Mise à jour du badge de mode
        self.badge_mode.setText(dev.mode_display.upper())
        self.badge_mode.setStyleSheet(self._badge_style(dev.color))

        # Titre et port
        loc = dev.port or dev.serial_number or dev.identifier
        self.lbl_headline.setText(f"{dev.badge_title}")
        self.lbl_port_value.setText(f"{loc} ({dev.description})")
        self.lbl_port_value.setStyleSheet(f"color: {dev.color}; font-size: 12px; font-weight: bold;")

        self.lbl_proto_value.setText(dev.protocol or dev.mode_display)
        self.lbl_proto_value.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px;")

        # Conseils contextuels selon le mode
        if dev.mode == DeviceMode.BROM:
            self.lbl_advice_value.setText("✅ Mode BROM actif : Parfait pour le déblocage FRP et le flash de firmware.")
            self.lbl_advice_value.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 11px;")
        elif dev.mode == DeviceMode.FASTBOOT:
            self.lbl_advice_value.setText("⚡ Mode Fastboot actif : Prêt pour le déblocage FRP OEM et les commandes bootloader.")
            self.lbl_advice_value.setStyleSheet(f"color: {COLOR_CYAN}; font-size: 11px;")
        elif dev.mode == DeviceMode.NORMAL:
            self.lbl_advice_value.setText("ℹ Mode Normal/AT actif : Pour une opération de flash bas-niveau, éteignez le téléphone et rebranchez.")
            self.lbl_advice_value.setStyleSheet(f"color: {COLOR_PURPLE}; font-size: 11px;")

    def on_device_disconnected(self):
        """Appelé quand l'appareil est déconnecté."""
        self.device_connected = False
        self.current_device = None

        self.badge_mode.setText("EN ATTENTE")
        self.badge_mode.setStyleSheet(self._badge_style(COLOR_TEXT_MUTED))

        self.lbl_headline.setText("En attente de connexion d'un appareil...")
        self.lbl_port_value.setText("Aucun")
        self.lbl_port_value.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")

        self.lbl_proto_value.setText("Scan automatique actif (BROM / Fastboot / Normal)")
        self.lbl_proto_value.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")

        self.lbl_advice_value.setText("Connectez l'appareil éteint avec Volume- pour le mode BROM, ou allumez en mode Fastboot.")
        self.lbl_advice_value.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-style: italic;")

    def _launch_frp_action(self):
        """Bascule sur l'onglet FRP et déclenche l'assistant de déblocage FRP."""
        main_win = self.window()
        if hasattr(main_win, "tabs"):
            main_win.tabs.setCurrentIndex(1)
        if hasattr(main_win, "frp_tab"):
            main_win.frp_tab._start_frp_reset()

    def _launch_factory_reset_action(self):
        """Bascule sur l'onglet FRP et déclenche l'assistant de Factory Reset."""
        main_win = self.window()
        if hasattr(main_win, "tabs"):
            main_win.tabs.setCurrentIndex(1)
        if hasattr(main_win, "frp_tab"):
            main_win.frp_tab._start_factory_reset()

    def _launch_read_info_action(self):
        """Bascule sur l'onglet Informations et déclenche la lecture avec assistant."""
        main_win = self.window()
        if hasattr(main_win, "tabs"):
            main_win.tabs.setCurrentIndex(3)
        if hasattr(main_win, "device_info_tab"):
            main_win.device_info_tab._on_read_info_clicked()

    def _go_to_flash(self):
        main_win = self.window()
        if hasattr(main_win, "tabs"):
            main_win.tabs.setCurrentIndex(2)
