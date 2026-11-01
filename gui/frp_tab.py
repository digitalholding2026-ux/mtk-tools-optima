# -*- coding: utf-8 -*-
"""
Onglet 2 : [FRP & Sécurité] pour Optima MTK Tool.
Propose deux méthodes distinctes et sécurisées de déverrouillage FRP :
  1. Méthode Fastboot       (Commandes OEM Bootloader)
  2. Méthode BROM/Preloader (Accès matériel direct MediaTek DA)
Comprend des avertissements visuels clairs et une barre d'avancement.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
    QPushButton, QTextEdit, QProgressBar, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from core.detector import ConnectedDevice, DeviceMode

# Palette de couleurs Optima Telecom
COLOR_BG_TAB = "#0f111a"
COLOR_BG_CARD = "#161a28"
COLOR_BG_INPUT = "#10131e"
COLOR_ACCENT = "#00a2ff"
COLOR_TEXT = "#e8eaf2"
COLOR_TEXT_MUTED = "#8a92a8"
COLOR_BORDER = "#252c40"
COLOR_SUCCESS = "#2ecc71"
COLOR_WARNING = "#f1c40f"
COLOR_WARNING_BG = "#211b0e"
COLOR_WARNING_BORDER = "#4d3810"
COLOR_ERROR = "#e74c3c"
COLOR_CYAN = "#00c3ff"


class FRPOperationWorker(QThread):
    """Worker d'arrière-plan pour exécuter l'action FRP sans figer l'interface."""
    progress = pyqtSignal(int)
    log = pyqtSignal(str, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, mode: DeviceMode, device: ConnectedDevice, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.device = device

    def run(self):
        try:
            from core.actions import erase_frp
            target_id = (
                self.device.port or
                self.device.serial_number or
                self.device.identifier if self.device else "COM3"
            )

            self.progress.emit(25)

            def _log_cb(msg: str, lvl: str = "info"):
                self.log.emit(msg, lvl)

            self.progress.emit(50)
            res = erase_frp(mode=self.mode, device_identifier=target_id, log_callback=_log_cb)
            self.progress.emit(100)

            self.finished.emit(res.success, res.message)
        except Exception as e:
            self.log.emit(f"[ERROR] Exception FRP : {str(e)}", "error")
            self.finished.emit(False, str(e))


class FRPResetTab(QWidget):
    """Onglet [FRP & Sécurité] de l'application."""

    def __init__(self, mtk_comm, parent=None):
        super().__init__(parent)
        self.mtk_comm = mtk_comm
        self.device_connected = False
        self.current_device: ConnectedDevice = None
        self.worker: FRPOperationWorker = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(16)

        # ── 1. Avertissement visuel clair (Atelier de maintenance) ───
        warning_banner = QFrame()
        warning_banner.setObjectName("warningBanner")
        warn_layout = QHBoxLayout(warning_banner)
        warn_layout.setContentsMargins(16, 12, 16, 12)
        warn_layout.setSpacing(14)

        lbl_warn_icon = QLabel("⚠️")
        lbl_warn_icon.setFont(QFont("Segoe UI Emoji", 20))
        lbl_warn_icon.setAlignment(Qt.AlignCenter)
        warn_layout.addWidget(lbl_warn_icon)

        warn_text_layout = QVBoxLayout()
        warn_text_layout.setSpacing(2)

        lbl_warn_title = QLabel("AVERTISSEMENT DE SÉCURITÉ FRP & COMPTE GOOGLE")
        lbl_warn_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_warn_title.setStyleSheet(f"color: {COLOR_WARNING};")

        lbl_warn_body = QLabel(
            "L'effacement de la partition FRP (Factory Reset Protection) supprime définitivement les identifiants "
            "du compte Google associé. Opération strictement réservée aux techniciens d'atelier autorisés.\n"
            "Vérifiez que le téléphone dispose d'au moins 30% de charge avant de lancer l'opération."
        )
        lbl_warn_body.setWordWrap(True)
        lbl_warn_body.setStyleSheet(f"color: #d1b87a; font-size: 11px;")

        warn_text_layout.addWidget(lbl_warn_title)
        warn_text_layout.addWidget(lbl_warn_body)
        warn_layout.addLayout(warn_text_layout)

        layout.addWidget(warning_banner)

        # ── 2. Grille des 2 méthodes claires de déblocage FRP ─────────
        methods_group = QGroupBox("Méthodes de déverrouillage disponibles")
        methods_group.setObjectName("methodsGroup")
        methods_layout = QGridLayout(methods_group)
        methods_layout.setContentsMargins(15, 18, 15, 18)
        methods_layout.setHorizontalSpacing(18)
        methods_layout.setVerticalSpacing(12)

        # --- Méthode A : Fastboot ---
        card_fb = QFrame()
        card_fb.setObjectName("methodCard")
        fb_layout = QVBoxLayout(card_fb)
        fb_layout.setContentsMargins(16, 16, 16, 16)
        fb_layout.setSpacing(10)

        lbl_fb_title = QLabel("⚡ Méthode Fastboot (Bootloader)")
        lbl_fb_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_fb_title.setStyleSheet(f"color: {COLOR_CYAN};")

        lbl_fb_desc = QLabel(
            "Idéal si le smartphone démarre déjà en mode Fastboot ou si le bootloader "
            "est déverrouillé. Exécute les commandes standard OEM d'effacement de la partition 'frp'."
        )
        lbl_fb_desc.setWordWrap(True)
        lbl_fb_desc.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")

        lbl_fb_guide = QLabel("Conditions : Téléphone allumé en mode Fastboot (Vol- & Power)")
        lbl_fb_guide.setStyleSheet(f"color: {COLOR_CYAN}; font-size: 10px; font-weight: bold;")

        self.btn_frp_fastboot = QPushButton("⚡ Effacer FRP (Méthode Fastboot)")
        self.btn_frp_fastboot.setObjectName("btnFastboot")
        self.btn_frp_fastboot.setFixedHeight(44)
        self.btn_frp_fastboot.setCursor(Qt.PointingHandCursor)
        self.btn_frp_fastboot.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_frp_fastboot.clicked.connect(self._on_frp_fastboot_clicked)

        fb_layout.addWidget(lbl_fb_title)
        fb_layout.addWidget(lbl_fb_desc)
        fb_layout.addWidget(lbl_fb_guide)
        fb_layout.addStretch()
        fb_layout.addWidget(self.btn_frp_fastboot)

        # --- Méthode B : BROM / Preloader ---
        card_brom = QFrame()
        card_brom.setObjectName("methodCard")
        brom_layout = QVBoxLayout(card_brom)
        brom_layout.setContentsMargins(16, 16, 16, 16)
        brom_layout.setSpacing(10)

        lbl_brom_title = QLabel("🛡️ Méthode BROM / Preloader (Direct DA)")
        lbl_brom_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_brom_title.setStyleSheet(f"color: {COLOR_SUCCESS};")

        lbl_brom_desc = QLabel(
            "Méthode universelle recommandée pour tous les processeurs MediaTek (MT65xx, MT67xx, MT68xx). "
            "Communique directement avec le BootROM matériel pour effacer la zone de persistance sans OS."
        )
        lbl_brom_desc.setWordWrap(True)
        lbl_brom_desc.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")

        lbl_brom_guide = QLabel("Conditions : Téléphone éteint + branchement USB avec Volume-")
        lbl_brom_guide.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 10px; font-weight: bold;")

        self.btn_frp_brom = QPushButton("🛡️ Effacer FRP (Méthode BROM/Preloader)")
        self.btn_frp_brom.setObjectName("btnBrom")
        self.btn_frp_brom.setFixedHeight(44)
        self.btn_frp_brom.setCursor(Qt.PointingHandCursor)
        self.btn_frp_brom.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_frp_brom.clicked.connect(self._on_frp_brom_clicked)

        brom_layout.addWidget(lbl_brom_title)
        brom_layout.addWidget(lbl_brom_desc)
        brom_layout.addWidget(lbl_brom_guide)
        brom_layout.addStretch()
        brom_layout.addWidget(self.btn_frp_brom)

        methods_layout.addWidget(card_fb, 0, 0)
        methods_layout.addWidget(card_brom, 0, 1)
        layout.addWidget(methods_group)

        # ── 3. Progression de l'opération ────────────────────────────
        prog_frame = QFrame()
        prog_layout = QVBoxLayout(prog_frame)
        prog_layout.setContentsMargins(0, 0, 0, 0)
        prog_layout.setSpacing(6)

        self.lbl_op_status = QLabel("Prêt pour le déverrouillage.")
        self.lbl_op_status.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)

        prog_layout.addWidget(self.lbl_op_status)
        prog_layout.addWidget(self.progress_bar)
        layout.addWidget(prog_frame)

        # ── 4. Journal d'opération dédié ─────────────────────────────
        log_group = QGroupBox("Journal d'exécution FRP")
        log_group.setObjectName("logGroup")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(15, 15, 15, 15)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setPlaceholderText("Les étapes techniques de déverrouillage s'afficheront ici en temps réel...")
        self.txt_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BG_INPUT};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 11px;
                padding: 8px;
            }}
        """)
        log_layout.addWidget(self.txt_log)
        layout.addWidget(log_group, stretch=1)

        self._apply_stylesheet()

    def _apply_stylesheet(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_BG_TAB};
                color: {COLOR_TEXT};
            }}
            QFrame#warningBanner {{
                background-color: {COLOR_WARNING_BG};
                border: 1px solid {COLOR_WARNING_BORDER};
                border-left: 4px solid {COLOR_WARNING};
                border-radius: 8px;
            }}
            QGroupBox#methodsGroup, QGroupBox#logGroup {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                font-weight: bold;
                color: {COLOR_TEXT};
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 6px;
                color: {COLOR_ACCENT};
            }}
            QFrame#methodCard {{
                background-color: #121522;
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
            QFrame#methodCard:hover {{
                border-color: {COLOR_ACCENT}88;
                background-color: #171b2b;
            }}
            QPushButton#btnFastboot {{
                background-color: #0b2d42;
                color: {COLOR_CYAN};
                border: 1px solid {COLOR_CYAN}88;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton#btnFastboot:hover {{
                background-color: #0d3d5b;
                border-color: {COLOR_CYAN};
                color: #ffffff;
            }}
            QPushButton#btnFastboot:pressed {{
                background-color: {COLOR_CYAN};
                color: #000000;
            }}
            QPushButton#btnBrom {{
                background-color: #0d3119;
                color: {COLOR_SUCCESS};
                border: 1px solid {COLOR_SUCCESS}88;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton#btnBrom:hover {{
                background-color: #124323;
                border-color: {COLOR_SUCCESS};
                color: #ffffff;
            }}
            QPushButton#btnBrom:pressed {{
                background-color: {COLOR_SUCCESS};
                color: #000000;
            }}
            QProgressBar {{
                background-color: {COLOR_BG_INPUT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_ACCENT};
                border-radius: 5px;
            }}
        """)

    # ------------------------------------------------------------------
    # Déclencheurs d'action
    # ------------------------------------------------------------------
    def _on_frp_fastboot_clicked(self):
        """Lance l'effacement FRP spécifiquement via la méthode Fastboot."""
        main_win = self.window()
        custom_instructions = (
            "1. Éteignez complètement le smartphone.\n"
            "2. Maintenez enfoncés simultanément [Volume Bas] et [Power].\n"
            "3. Dès l'apparition du logo 'FASTBOOT', connectez le câble USB."
        )
        if hasattr(main_win, "run_action_with_assistant"):
            main_win.run_action_with_assistant(
                action_name="Effacer FRP (Fastboot)",
                operation_func=lambda dev: self._execute_frp(DeviceMode.FASTBOOT, dev),
                target_modes=[DeviceMode.FASTBOOT],
                custom_instructions=custom_instructions
            )
        else:
            self._execute_frp(DeviceMode.FASTBOOT, self.current_device)

    def _on_frp_brom_clicked(self):
        """Lance l'effacement FRP spécifiquement via la méthode BROM/Preloader."""
        main_win = self.window()
        custom_instructions = (
            "1. Éteignez complètement le smartphone.\n"
            "2. Maintenez enfoncé [Volume Bas] (ou [Volume Haut + Bas] selon le modèle).\n"
            "3. Insérez le câble USB relié au PC tout en maintenant la touche."
        )
        if hasattr(main_win, "run_action_with_assistant"):
            main_win.run_action_with_assistant(
                action_name="Effacer FRP (BROM/Preloader)",
                operation_func=lambda dev: self._execute_frp(DeviceMode.BROM, dev),
                target_modes=[DeviceMode.BROM],
                custom_instructions=custom_instructions
            )
        else:
            self._execute_frp(DeviceMode.BROM, self.current_device)

    # ------------------------------------------------------------------
    # Exécution de l'opération
    # ------------------------------------------------------------------
    def _execute_frp(self, mode: DeviceMode, device: ConnectedDevice):
        """Démarre le worker d'effacement FRP."""
        self.btn_frp_fastboot.setEnabled(False)
        self.btn_frp_brom.setEnabled(False)
        self.progress_bar.setValue(10)
        self.lbl_op_status.setText(f"Exécution du déblocage FRP ({mode.value})...")
        self.txt_log.clear()

        self.worker = FRPOperationWorker(mode, device)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log.connect(self._on_worker_log)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_log(self, msg: str, level: str):
        color = COLOR_TEXT
        if level == "success":
            color = COLOR_SUCCESS
        elif level == "error":
            color = COLOR_ERROR
        elif level == "warning":
            color = COLOR_WARNING
        elif level == "info" and msg.startswith("[+]"):
            color = COLOR_ACCENT

        self.txt_log.append(f'<span style="color:{color}">• {msg}</span>')

        main_win = self.window()
        if hasattr(main_win, "log_panel"):
            main_win.log_panel.add_log(msg, level)

    def _on_worker_finished(self, success: bool, message: str):
        self.btn_frp_fastboot.setEnabled(True)
        self.btn_frp_brom.setEnabled(True)

        if success:
            self.progress_bar.setValue(100)
            self.lbl_op_status.setText("✅ Déblocage FRP terminé avec succès.")
            QMessageBox.information(
                self,
                "FRP Débloqué avec Succès",
                f"<b>Succès :</b> {message}<br><br>"
                "Le smartphone va redémarrer automatiquement sans configuration de compte Google."
            )
        else:
            self.lbl_op_status.setText("❌ Échec de l'opération FRP.")
            QMessageBox.critical(
                self,
                "Échec de l'opération FRP",
                f"L'opération a échoué avec l'erreur suivante :<br><br><b>{message}</b><br><br>"
                "Vérifiez la connexion USB et que le pilote MTK VCOM ou Fastboot est bien installé."
            )

    # ------------------------------------------------------------------
    # Synchronisation de connexion
    # ------------------------------------------------------------------
    def on_device_connected(self, device: ConnectedDevice):
        self.device_connected = True
        self.current_device = device
        self.lbl_op_status.setText(f"Appareil connecté : {device.badge_title}")

    def on_device_disconnected(self):
        self.device_connected = False
        self.current_device = None
        self.lbl_op_status.setText("Prêt pour le déverrouillage.")
