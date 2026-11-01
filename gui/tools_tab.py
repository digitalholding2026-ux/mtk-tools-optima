# -*- coding: utf-8 -*-
"""
Onglet 3 : [Outils & Redémarrage] pour Optima MTK Tool.
Comprend :
  - Factory Reset (Formatage d'usine / effacement complet des données utilisateur)
  - Options de redémarrage direct :
      * Reboot Normal (Système)
      * Reboot Fastboot (Bootloader)
      * Reboot Recovery (Récupération)
  - Section Outil Flash Scatter (Fichiers firmware MediaTek)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
    QPushButton, QTextEdit, QProgressBar, QMessageBox, QFrame, QFileDialog, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
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
COLOR_WARNING = "#f1c40f"
COLOR_ERROR = "#e74c3c"
COLOR_CYAN = "#00c3ff"
COLOR_PURPLE = "#a29bfe"


class ToolsOperationWorker(QThread):
    """Worker d'arrière-plan pour Factory Reset ou Flash."""
    progress = pyqtSignal(int)
    log = pyqtSignal(str, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, action_type: str, device: ConnectedDevice, extra_data: str = "", parent=None):
        super().__init__(parent)
        self.action_type = action_type
        self.device = device
        self.extra_data = extra_data

    def run(self):
        try:
            target_id = (
                self.device.port or
                self.device.serial_number or
                self.device.identifier if self.device else "COM3"
            )
            mode = self.device.mode if self.device else DeviceMode.BROM

            def _log_cb(msg: str, lvl: str = "info"):
                self.log.emit(msg, lvl)

            if self.action_type == "factory_reset":
                from core.actions import factory_reset
                self.progress.emit(25)
                res = factory_reset(mode=mode, device_identifier=target_id, log_callback=_log_cb)
                self.progress.emit(100)
                self.finished.emit(res.success, res.message)

            elif self.action_type == "reboot":
                from core.actions import reboot_device
                self.progress.emit(30)
                res = reboot_device(mode=mode, device_identifier=target_id, target_reboot=self.extra_data, log_callback=_log_cb)
                self.progress.emit(100)
                self.finished.emit(res.success, res.message)

        except Exception as e:
            self.log.emit(f"[ERROR] Exception opération : {str(e)}", "error")
            self.finished.emit(False, str(e))


class ToolsTab(QWidget):
    """Onglet [Outils & Redémarrage] pour les opérations d'atelier."""

    def __init__(self, mtk_comm, parent=None):
        super().__init__(parent)
        self.mtk_comm = mtk_comm
        self.device_connected = False
        self.current_device: ConnectedDevice = None
        self.worker: ToolsOperationWorker = None
        self.firmware_path: str = ""

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 20, 25, 20)
        layout.setSpacing(16)

        # ── Rangée 1 : Factory Reset & Redémarrage côte à côte ────────
        top_grid = QGridLayout()
        top_grid.setHorizontalSpacing(18)
        top_grid.setVerticalSpacing(12)

        # ─────────────────────────────────────────────────────────────
        # Section A : Factory Reset (Formatage d'usine)
        # ─────────────────────────────────────────────────────────────
        reset_group = QGroupBox("Réinitialisation Matérielle")
        reset_group.setObjectName("resetGroup")
        reset_layout = QVBoxLayout(reset_group)
        reset_layout.setContentsMargins(16, 16, 16, 16)
        reset_layout.setSpacing(10)

        lbl_reset_title = QLabel("🧹 Factory Reset (Formatage d'usine)")
        lbl_reset_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        lbl_reset_title.setStyleSheet(f"color: {COLOR_ERROR};")

        lbl_reset_warn = QLabel(
            "⚠️ ATTENTION : Efface l'intégralité des données utilisateur (userdata, cache, "
            "applications, photos, comptes). Cette opération remet le téléphone à neuf."
        )
        lbl_reset_warn.setWordWrap(True)
        lbl_reset_warn.setStyleSheet("color: #e59990; font-size: 11px;")

        lbl_reset_modes = QLabel("Compatible : Mode BROM (téléphone éteint) ou Fastboot")
        lbl_reset_modes.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-weight: bold;")

        self.btn_factory_reset = QPushButton("🧹 Lancer le Factory Reset")
        self.btn_factory_reset.setObjectName("btnReset")
        self.btn_factory_reset.setFixedHeight(44)
        self.btn_factory_reset.setCursor(Qt.PointingHandCursor)
        self.btn_factory_reset.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_factory_reset.clicked.connect(self._on_factory_reset_clicked)

        reset_layout.addWidget(lbl_reset_title)
        reset_layout.addWidget(lbl_reset_warn)
        reset_layout.addWidget(lbl_reset_modes)
        reset_layout.addStretch()
        reset_layout.addWidget(self.btn_factory_reset)

        top_grid.addWidget(reset_group, 0, 0)

        # ─────────────────────────────────────────────────────────────
        # Section B : Options de Redémarrage (Reboot)
        # ─────────────────────────────────────────────────────────────
        reboot_group = QGroupBox("Options de Redémarrage Rapide")
        reboot_group.setObjectName("rebootGroup")
        reboot_layout = QVBoxLayout(reboot_group)
        reboot_layout.setContentsMargins(16, 16, 16, 16)
        reboot_layout.setSpacing(10)

        lbl_reboot_info = QLabel("Envoyez des commandes de redémarrage direct selon le mode actif :")
        lbl_reboot_info.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        reboot_layout.addWidget(lbl_reboot_info)

        # 3 boutons de reboot
        btn_reboot_grid = QHBoxLayout()
        btn_reboot_grid.setSpacing(10)

        self.btn_reboot_normal = QPushButton("🔄 Reboot Normal")
        self.btn_reboot_normal.setObjectName("btnRebootNormal")
        self.btn_reboot_normal.setFixedHeight(44)
        self.btn_reboot_normal.setCursor(Qt.PointingHandCursor)
        self.btn_reboot_normal.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.btn_reboot_normal.setToolTip("Redémarre l'appareil normalement dans le système d'exploitation Android.")
        self.btn_reboot_normal.clicked.connect(lambda: self._on_reboot_clicked("normal"))

        self.btn_reboot_fastboot = QPushButton("⚡ Reboot Fastboot")
        self.btn_reboot_fastboot.setObjectName("btnRebootFastboot")
        self.btn_reboot_fastboot.setFixedHeight(44)
        self.btn_reboot_fastboot.setCursor(Qt.PointingHandCursor)
        self.btn_reboot_fastboot.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.btn_reboot_fastboot.setToolTip("Redémarre l'appareil dans le chargeur d'amorçage (Bootloader / Fastboot).")
        self.btn_reboot_fastboot.clicked.connect(lambda: self._on_reboot_clicked("fastboot"))

        self.btn_reboot_recovery = QPushButton("🛠️ Reboot Recovery")
        self.btn_reboot_recovery.setObjectName("btnRebootRecovery")
        self.btn_reboot_recovery.setFixedHeight(44)
        self.btn_reboot_recovery.setCursor(Qt.PointingHandCursor)
        self.btn_reboot_recovery.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.btn_reboot_recovery.setToolTip("Redémarre l'appareil en mode Récupération (Recovery Stock / TWRP).")
        self.btn_reboot_recovery.clicked.connect(lambda: self._on_reboot_clicked("recovery"))

        btn_reboot_grid.addWidget(self.btn_reboot_normal)
        btn_reboot_grid.addWidget(self.btn_reboot_fastboot)
        btn_reboot_grid.addWidget(self.btn_reboot_recovery)
        reboot_layout.addLayout(btn_reboot_grid)

        lbl_reboot_note = QLabel("Supporte : Fastboot, ADB (Débogage actif) et liaison série BROM.")
        lbl_reboot_note.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-style: italic;")
        reboot_layout.addWidget(lbl_reboot_note)
        reboot_layout.addStretch()

        top_grid.addWidget(reboot_group, 0, 1)
        layout.addLayout(top_grid)

        # ─────────────────────────────────────────────────────────────
        # Section C : Outil Flash Firmware (Scatter MTK)
        # ─────────────────────────────────────────────────────────────
        flash_group = QGroupBox("Outil Flash Firmware (Scatter MTK)")
        flash_group.setObjectName("flashGroup")
        flash_layout = QVBoxLayout(flash_group)
        flash_layout.setContentsMargins(16, 14, 16, 14)
        flash_layout.setSpacing(10)

        flash_input_layout = QHBoxLayout()
        flash_input_layout.setSpacing(10)

        self.txt_firmware = QLineEdit()
        self.txt_firmware.setPlaceholderText("Sélectionnez le fichier scatter Android (ex: MT6765_Android_scatter.txt)...")
        self.txt_firmware.setReadOnly(True)
        self.txt_firmware.setFixedHeight(38)
        self.txt_firmware.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_BG_INPUT};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding-left: 10px;
                font-size: 11px;
            }}
        """)

        btn_browse = QPushButton("📁 Parcourir...")
        btn_browse.setFixedHeight(38)
        btn_browse.setFixedWidth(120)
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.setFont(QFont("Segoe UI", 10, QFont.Bold))
        btn_browse.clicked.connect(self._on_browse_scatter)

        self.btn_start_flash = QPushButton("⚡ Flasher Firmware")
        self.btn_start_flash.setObjectName("btnFlash")
        self.btn_start_flash.setFixedHeight(38)
        self.btn_start_flash.setFixedWidth(160)
        self.btn_start_flash.setCursor(Qt.PointingHandCursor)
        self.btn_start_flash.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.btn_start_flash.setEnabled(False)
        self.btn_start_flash.clicked.connect(self._on_start_flash_clicked)

        flash_input_layout.addWidget(self.txt_firmware)
        flash_input_layout.addWidget(btn_browse)
        flash_input_layout.addWidget(self.btn_start_flash)
        flash_layout.addLayout(flash_input_layout)

        layout.addWidget(flash_group)

        # ── Barre de progression & Journal ───────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        log_group = QGroupBox("Journal des opérations et outils")
        log_group.setObjectName("logGroup")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(15, 12, 15, 12)

        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setPlaceholderText("Les comptes-rendus des actions de maintenance s'afficheront ici...")
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
            QGroupBox {{
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
            QPushButton#btnReset {{
                background-color: #3b1414;
                color: {COLOR_ERROR};
                border: 1px solid {COLOR_ERROR}88;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton#btnReset:hover {{
                background-color: #551c1c;
                border-color: {COLOR_ERROR};
                color: #ffffff;
            }}
            QPushButton#btnReset:pressed {{
                background-color: {COLOR_ERROR};
                color: #ffffff;
            }}
            QPushButton#btnRebootNormal, QPushButton#btnRebootFastboot, QPushButton#btnRebootRecovery {{
                background-color: #1a2032;
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
            }}
            QPushButton#btnRebootNormal:hover {{
                border-color: {COLOR_SUCCESS};
                color: {COLOR_SUCCESS};
                background-color: #12281c;
            }}
            QPushButton#btnRebootFastboot:hover {{
                border-color: {COLOR_CYAN};
                color: {COLOR_CYAN};
                background-color: #0e2a3b;
            }}
            QPushButton#btnRebootRecovery:hover {{
                border-color: {COLOR_PURPLE};
                color: {COLOR_PURPLE};
                background-color: #241c38;
            }}
            QPushButton#btnFlash {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 6px;
            }}
            QPushButton#btnFlash:hover {{
                background-color: {COLOR_ACCENT_HOVER};
            }}
            QPushButton#btnFlash:disabled {{
                background-color: #252c40;
                color: {COLOR_TEXT_MUTED};
            }}
            QProgressBar {{
                background-color: {COLOR_BG_INPUT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_ACCENT};
                border-radius: 4px;
            }}
        """)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _on_factory_reset_clicked(self):
        """Demande confirmation puis lance le Factory Reset avec l'assistant JIT si besoin."""
        reply = QMessageBox.warning(
            self,
            "Confirmation de Réinitialisation d'Usine",
            "<b>ATTENTION : TOUTES LES DONNÉES DU TÉLÉPHONE SERONT DÉTRUITES.</b><br><br>"
            "Cette action efface définitivement :<br>"
            "• Photos, vidéos, musique et fichiers personnels<br>"
            "• Applications et comptes enregistrés<br>"
            "• Paramètres système et verrouillages écran<br><br>"
            "Êtes-vous certain de vouloir procéder au formatage complet ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        main_win = self.window()
        if hasattr(main_win, "run_action_with_assistant"):
            main_win.run_action_with_assistant(
                action_name="Factory Reset",
                operation_func=self._execute_factory_reset,
                target_modes=[DeviceMode.BROM, DeviceMode.FASTBOOT]
            )
        else:
            self._execute_factory_reset(self.current_device)

    def _execute_factory_reset(self, device: ConnectedDevice):
        self.btn_factory_reset.setEnabled(False)
        self.progress_bar.setValue(15)
        self.txt_log.clear()

        self.worker = ToolsOperationWorker("factory_reset", device)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log.connect(self._on_worker_log)
        self.worker.finished.connect(self._on_factory_reset_finished)
        self.worker.start()

    def _on_factory_reset_finished(self, success: bool, message: str):
        self.btn_factory_reset.setEnabled(True)
        if success:
            self.progress_bar.setValue(100)
            QMessageBox.information(
                self,
                "Factory Reset Terminé",
                f"<b>Succès :</b> {message}<br><br>Le smartphone redémarre avec les paramètres d'usine d'origine."
            )
        else:
            QMessageBox.critical(
                self,
                "Échec du Factory Reset",
                f"L'opération a échoué :<br><br><b>{message}</b>"
            )

    def _on_reboot_clicked(self, target: str):
        """Déclenche le redémarrage direct vers la cible choisie."""
        label = {"normal": "Normal", "fastboot": "Fastboot", "recovery": "Recovery"}.get(target, target)
        self._append_log(f"[+] Envoi de l'instruction de redémarrage ({label})...", "info")

        if self.current_device:
            from core.actions import reboot_device
            target_id = self.current_device.port or self.current_device.serial_number or self.current_device.identifier
            res = reboot_device(
                mode=self.current_device.mode,
                device_identifier=target_id,
                target_reboot=target,
                log_callback=self._append_log
            )
            if res.success:
                self._append_log(f"[SUCCESS] Redémarrage vers {label} envoyé.", "success")
            else:
                self._append_log(f"[ERROR] Échec redémarrage : {res.message}", "error")
        else:
            main_win = self.window()
            if hasattr(main_win, "run_action_with_assistant"):
                main_win.run_action_with_assistant(
                    action_name=f"Reboot {label}",
                    operation_func=lambda dev: self._execute_reboot(dev, target),
                    target_modes=[DeviceMode.BROM, DeviceMode.FASTBOOT, DeviceMode.ADB, DeviceMode.NORMAL]
                )
            else:
                self._append_log("[WARNING] Aucun appareil connecté pour le redémarrage.", "warning")

    def _execute_reboot(self, device: ConnectedDevice, target: str):
        self.worker = ToolsOperationWorker("reboot", device, extra_data=target)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log.connect(self._on_worker_log)
        self.worker.finished.connect(lambda s, m: self._append_log(f"[{'SUCCESS' if s else 'ERROR'}] {m}", "success" if s else "error"))
        self.worker.start()

    def _on_browse_scatter(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner le fichier Scatter MediaTek",
            "",
            "Scatter MTK (*scatter*.txt *.txt);;Tous les fichiers (*)"
        )
        if file_path:
            self.firmware_path = file_path
            self.txt_firmware.setText(file_path)
            self.btn_start_flash.setEnabled(True)

    def _on_start_flash_clicked(self):
        if not self.firmware_path:
            QMessageBox.warning(self, "Fichier manquant", "Veuillez sélectionner un fichier scatter MTK valide.")
            return

        main_win = self.window()
        if hasattr(main_win, "run_action_with_assistant"):
            main_win.run_action_with_assistant(
                action_name="Flash Firmware",
                operation_func=self._execute_flash,
                target_modes=[DeviceMode.BROM]
            )
        else:
            self._execute_flash(self.current_device)

    def _execute_flash(self, device: ConnectedDevice):
        self._append_log(f"[+] Démarrage du flash firmware ({self.firmware_path})...", "info")
        self.progress_bar.setValue(20)
        self.mtk_comm.flash_firmware(self.firmware_path, callback=lambda s, m: self._append_log(f"[{'SUCCESS' if s else 'ERROR'}] {m}", "success" if s else "error"))
        self.progress_bar.setValue(100)

    def _on_worker_log(self, msg: str, level: str):
        self._append_log(msg, level)

    def _append_log(self, msg: str, level: str):
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

    # ------------------------------------------------------------------
    # Synchronisation de connexion
    # ------------------------------------------------------------------
    def on_device_connected(self, device: ConnectedDevice):
        self.device_connected = True
        self.current_device = device

    def on_device_disconnected(self):
        self.device_connected = False
        self.current_device = None
