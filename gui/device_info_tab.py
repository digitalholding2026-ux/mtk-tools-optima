# -*- coding: utf-8 -*-
"""
Onglet 1 : [Infos & Diagnostic] pour Optima MTK Tool.
Affiche les spécifications de l'appareil dans une grille moderne et claire :
  - Modèle / Nom
  - Chipset / Processeur MediaTek
  - IMEI / Numéro de série
  - Version Android
Bouton unique ergonomique pour la lecture instantanée ou guidée des informations.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QTextEdit, QFrame, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.detector import ConnectedDevice, DeviceMode

# Palette de couleurs Optima Telecom
COLOR_BG_TAB = "#0f111a"
COLOR_BG_CARD = "#161a28"
COLOR_BG_INPUT = "#10131e"
COLOR_ACCENT = "#00a2ff"
COLOR_ACCENT_HOVER = "#0088cc"
COLOR_TEXT = "#e8eaf2"
COLOR_TEXT_MUTED = "#8a92a8"
COLOR_BORDER = "#252c40"
COLOR_SUCCESS = "#2ecc71"
COLOR_CYAN = "#00c3ff"
COLOR_WARNING = "#f1c40f"
COLOR_PURPLE = "#a29bfe"


class SpecCard(QFrame):
    """Carte d'affichage moderne pour une spécification technique."""

    def __init__(self, title: str, default_value: str = "—", icon: str = "📱", parent=None):
        super().__init__(parent)
        self.setObjectName("specCard")
        self.setMinimumHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)

        # Icône visuelle
        self.lbl_icon = QLabel(icon)
        self.lbl_icon.setFont(QFont("Segoe UI Emoji", 20))
        self.lbl_icon.setFixedWidth(36)
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_icon)

        # Textes (Libellé + Valeur)
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;")

        self.lbl_val = QLabel(default_value)
        self.lbl_val.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 13px; font-weight: bold;")
        self.lbl_val.setTextInteractionFlags(Qt.TextSelectableByMouse)

        text_layout.addWidget(self.lbl_title)
        text_layout.addWidget(self.lbl_val)
        layout.addLayout(text_layout)
        layout.addStretch()

        self.setStyleSheet(f"""
            QFrame#specCard {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
            QFrame#specCard:hover {{
                border-color: {COLOR_ACCENT}88;
                background-color: #1a1f30;
            }}
        """)

    def set_value(self, val: str, color: str = COLOR_TEXT):
        """Met à jour la valeur affichée avec une couleur optionnelle."""
        self.lbl_val.setText(val or "—")
        self.lbl_val.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")


class DeviceInfoTab(QWidget):
    """Onglet [Infos & Diagnostic] de l'application Optima MTK Tool."""

    def __init__(self, mtk_comm, parent=None):
        super().__init__(parent)
        self.mtk_comm = mtk_comm
        self.device_connected = False
        self.current_device: ConnectedDevice = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(16)

        # ── 1. Barre d'action supérieure avec bouton unique ───────────
        action_bar = QFrame()
        action_bar.setObjectName("actionBar")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(18, 14, 18, 14)
        action_layout.setSpacing(15)

        action_desc_layout = QVBoxLayout()
        action_desc_layout.setSpacing(2)

        lbl_desc_title = QLabel("Diagnostic & Identification Matérielle")
        lbl_desc_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_desc_title.setStyleSheet(f"color: {COLOR_TEXT};")

        lbl_desc_sub = QLabel("Lecture directe des registres matériels (BROM, Fastboot getvar ou ADB).")
        lbl_desc_sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")

        action_desc_layout.addWidget(lbl_desc_title)
        action_desc_layout.addWidget(lbl_desc_sub)
        action_layout.addLayout(action_desc_layout)
        action_layout.addStretch()

        # Bouton unique "Lire les informations"
        self.btn_read_info = QPushButton("📋 Lire les informations")
        self.btn_read_info.setObjectName("btnReadInfo")
        self.btn_read_info.setCursor(Qt.PointingHandCursor)
        self.btn_read_info.setMinimumHeight(40)
        self.btn_read_info.setMinimumWidth(220)
        self.btn_read_info.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_read_info.clicked.connect(self._on_read_info_clicked)
        action_layout.addWidget(self.btn_read_info)

        layout.addWidget(action_bar)

        # ── 2. Grille des 4 spécifications principales (Champs dédiés) ─
        grid_frame = QFrame()
        grid_layout = QGridLayout(grid_frame)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setHorizontalSpacing(15)
        grid_layout.setVerticalSpacing(12)

        # Champ 1 : Modèle / Nom
        self.card_model = SpecCard("Modèle de l'appareil", "Non identifié", "📱")
        # Champ 2 : Chipset / Processeur MediaTek
        self.card_chip = SpecCard("Chipset / Processeur", "En attente de lecture", "⚡")
        # Champ 3 : IMEI / N° Série
        self.card_imei = SpecCard("IMEI / N° de Série", "—", "🔑")
        # Champ 4 : Version Android
        self.card_android = SpecCard("Version Android", "—", "🤖")

        grid_layout.addWidget(self.card_model, 0, 0)
        grid_layout.addWidget(self.card_chip, 0, 1)
        grid_layout.addWidget(self.card_imei, 1, 0)
        grid_layout.addWidget(self.card_android, 1, 1)

        layout.addWidget(grid_frame)

        # ── 3. Spécifications de connexion & Protocole (Rangée secondaire) ──
        sub_grid = QGridLayout()
        sub_grid.setContentsMargins(0, 0, 0, 0)
        sub_grid.setHorizontalSpacing(15)
        sub_grid.setVerticalSpacing(12)

        self.card_mode = SpecCard("Mode de connexion", "Déconnecté", "🔌")
        self.card_port = SpecCard("Port / Liaison active", "Aucun", "💻")
        self.card_proto = SpecCard("Protocole actif", "En veille", "🌐")
        self.card_id = SpecCard("Identifiant Matériel", "—", "🏷️")

        sub_grid.addWidget(self.card_mode, 0, 0)
        sub_grid.addWidget(self.card_port, 0, 1)
        sub_grid.addWidget(self.card_proto, 0, 2)
        sub_grid.addWidget(self.card_id, 0, 3)

        layout.addLayout(sub_grid)

        # ── 4. Détails techniques & Rapport de diagnostic ────────────
        detail_group = QGroupBox("Rapport d'inspection bas-niveau")
        detail_group.setObjectName("detailGroup")
        detail_layout = QVBoxLayout(detail_group)
        detail_layout.setContentsMargins(15, 15, 15, 15)

        self.txt_details = QTextEdit()
        self.txt_details.setReadOnly(True)
        self.txt_details.setPlaceholderText(
            "Aucune analyse disponible. Cliquez sur « Lire les informations » "
            "ou branchez un appareil pour générer le rapport d'identification complet."
        )
        self.txt_details.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BG_INPUT};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 11px;
                padding: 10px;
            }}
        """)
        detail_layout.addWidget(self.txt_details)
        layout.addWidget(detail_group, stretch=1)

        self._apply_stylesheet()

    def _apply_stylesheet(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_BG_TAB};
                color: {COLOR_TEXT};
            }}
            QFrame#actionBar {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
            QPushButton#btnReadInfo {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }}
            QPushButton#btnReadInfo:hover {{
                background-color: {COLOR_ACCENT_HOVER};
            }}
            QPushButton#btnReadInfo:pressed {{
                background-color: #0070b8;
            }}
            QGroupBox#detailGroup {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                margin-top: 12px;
                font-weight: bold;
                color: {COLOR_TEXT};
                padding-top: 15px;
            }}
            QGroupBox#detailGroup::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 6px;
                color: {COLOR_ACCENT};
            }}
        """)

    # ------------------------------------------------------------------
    # Événements & Actualisation
    # ------------------------------------------------------------------
    def _on_read_info_clicked(self):
        """Déclenche la lecture des informations avec l'assistant JIT si besoin."""
        main_win = self.window()
        if hasattr(main_win, "run_action_with_assistant"):
            main_win.run_action_with_assistant(
                action_name="Lire Infos",
                operation_func=self._execute_read_info_with_device,
                target_modes=[DeviceMode.BROM, DeviceMode.FASTBOOT, DeviceMode.ADB, DeviceMode.NORMAL]
            )
        else:
            self._refresh_info()

    def _execute_read_info_with_device(self, device: ConnectedDevice):
        """Exécute la lecture lorsque l'appareil est détecté."""
        self.device_connected = True
        self.current_device = device
        self._refresh_info()

    def _refresh_info(self):
        """Interroge MTKCommunication et met à jour tous les champs dédiés."""
        if not self.device_connected or not self.current_device:
            return

        dev = self.current_device
        raw_info = self.mtk_comm.read_device_info()

        # 1. Modèle
        model_name = raw_info.get("name") or raw_info.get("model") or dev.description
        if dev.details.get("product_name"):
            model_name = dev.details["product_name"]
        self.card_model.set_value(model_name, COLOR_SUCCESS)

        # 2. Chipset
        chip_name = raw_info.get("chip") or raw_info.get("chipset") or "MediaTek MTK"
        if dev.details.get("hw_code_name"):
            chip_name = dev.details["hw_code_name"]
        self.card_chip.set_value(chip_name, COLOR_CYAN)

        # 3. IMEI / N° Série
        imei_val = raw_info.get("imei") or raw_info.get("serial") or dev.serial_number or "—"
        self.card_imei.set_value(imei_val, COLOR_TEXT)

        # 4. Version Android
        android_ver = raw_info.get("android") or raw_info.get("android_version") or "—"
        self.card_android.set_value(android_ver, COLOR_TEXT)

        # Cartes secondaires
        self.card_mode.set_value(dev.mode_display, dev.color)
        self.card_port.set_value(dev.port or dev.serial_number or dev.identifier, COLOR_TEXT)
        self.card_proto.set_value(dev.protocol or raw_info.get("protocol", "Standard"), COLOR_PURPLE)

        id_str = f"VID:{dev.vid:04X} PID:{dev.pid:04X}" if (dev.vid and dev.pid) else (dev.serial_number or dev.identifier)
        self.card_id.set_value(id_str, COLOR_TEXT_MUTED)

        # Rapport textuel
        self.txt_details.clear()
        self.txt_details.append("=================================================================")
        self.txt_details.append(f"  RAPPORT D'IDENTIFICATION MATÉRIELLE — OPTIMA MTK TOOL")
        self.txt_details.append("=================================================================")
        self.txt_details.append(f"• Modèle détecté       : {model_name}")
        self.txt_details.append(f"• Processeur / Chipset : {chip_name}")
        self.txt_details.append(f"• Mode de connexion    : {dev.mode_display} ({dev.mode.value})")
        self.txt_details.append(f"• Port / Interface     : {dev.port or dev.identifier}")
        if dev.serial_number:
            self.txt_details.append(f"• Numéro de Série USB  : {dev.serial_number}")
        if dev.vid and dev.pid:
            self.txt_details.append(f"• Identifiants USB     : VendorID=0x{dev.vid:04X}, ProductID=0x{dev.pid:04X}")
        if dev.manufacturer:
            self.txt_details.append(f"• Fabricant            : {dev.manufacturer}")
        if android_ver != "—":
            self.txt_details.append(f"• Version OS Android   : {android_ver}")
        self.txt_details.append(f"• Protocole utilisé    : {dev.protocol or 'MediaTek Comm'}")
        self.txt_details.append("-----------------------------------------------------------------")
        self.txt_details.append("[SUCCESS] Diagnostic terminé. Prêt pour les opérations de maintenance.")

    def on_device_connected(self, device: ConnectedDevice):
        """Appelé en temps réel lors du branchement d'un appareil."""
        self.device_connected = True
        self.current_device = device
        self._refresh_info()

    def on_device_disconnected(self):
        """Appelé en temps réel lors de la déconnexion."""
        self.device_connected = False
        self.current_device = None

        self.card_model.set_value("Non identifié")
        self.card_chip.set_value("En attente de lecture")
        self.card_imei.set_value("—")
        self.card_android.set_value("—")
        self.card_mode.set_value("Déconnecté", COLOR_TEXT_MUTED)
        self.card_port.set_value("Aucun")
        self.card_proto.set_value("En veille")
        self.card_id.set_value("—")

        self.txt_details.clear()
        self.txt_details.setPlaceholderText(
            "Aucune analyse disponible. Cliquez sur « Lire les informations » "
            "ou branchez un appareil pour générer le rapport d'identification complet."
        )
