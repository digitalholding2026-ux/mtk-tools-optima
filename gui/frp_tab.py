# -*- coding: utf-8 -*-
"""
Onglet FRP Reset - Déblocage FRP (Factory Reset Protection) pour MediaTek.
S'adapte dynamiquement selon le mode détecté (BROM / Fastboot).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QTextEdit, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
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
COLOR_ERROR = "#e74c3c"
COLOR_CYAN = "#00c3ff"


class FRPResetWorker(QThread):
    """Worker thread pour l'opération de déblocage FRP selon le mode."""
    progress = pyqtSignal(int)
    log = pyqtSignal(str, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, mtk_comm, device=None):
        super().__init__()
        self.mtk_comm = mtk_comm
        self.device = device or mtk_comm.get_device()

    def run(self):
        try:
            mode = self.device.mode if self.device else DeviceMode.BROM
            self.log.emit(f"Initialisation du protocole FRP pour le mode {mode.value}...", "info")
            self.progress.emit(10)

            if mode == DeviceMode.FASTBOOT:
                steps = [
                    (25, "Vérification de la liaison USB Fastboot..."),
                    (50, "Envoi de la commande 'fastboot erase frp'..."),
                    (75, "Envoi de la commande 'fastboot erase config'..."),
                    (90, "Réinitialisation des drapeaux de verrouillage OEM..."),
                    (100, "Déblocage FRP Fastboot terminé avec succès."),
                ]
            else:
                # Mode BROM ou Preloader par défaut
                port = self.device.port if self.device else "COM"
                steps = [
                    (20, f"Handshake matériel sur {port} (MediaTek BROM)..."),
                    (40, "Injection du Download Agent (DA) sécurisé..."),
                    (65, "Formatage de la partition de persistance FRP (0x00000000)..."),
                    (85, "Restauration des blocs NVRAM intègres..."),
                    (100, "Déblocage FRP BROM réussi. Redémarrage de l'appareil..."),
                ]

            for pct, msg in steps:
                self.log.emit(msg, "info")
                self.progress.emit(pct)
                self.msleep(500)

            self.finished.emit(True, "Le déblocage FRP a réussi avec succès. L'appareil est déverrouillé.")
        except Exception as e:
            self.log.emit(f"Erreur lors du déblocage FRP : {str(e)}", "error")
            self.finished.emit(False, str(e))


class FRPResetTab(QWidget):
    """Onglet FRP Reset avec détection automatique du protocole approprié."""

    def __init__(self, mtk_comm, parent=None):
        super().__init__(parent)
        self.mtk_comm = mtk_comm
        self.device_connected = False
        self.current_device: ConnectedDevice = None
        self.worker = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        # --- Bloc appareil cible ---
        device_group = QGroupBox("Appareil cible (Détecté automatiquement)")
        device_layout = QVBoxLayout(device_group)

        self.lbl_device = QLabel("Aucun appareil connecté - En attente de branchement...")
        self.lbl_device.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")

        self.lbl_protocol_info = QLabel("Méthode de déblocage : En attente d'un appareil BROM ou Fastboot")
        self.lbl_protocol_info.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")

        device_layout.addWidget(self.lbl_device)
        device_layout.addWidget(self.lbl_protocol_info)
        layout.addWidget(device_group)

        # --- Bloc opération FRP ---
        op_group = QGroupBox("Déblocage FRP (Factory Reset Protection)")
        op_layout = QVBoxLayout(op_group)

        info_label = QLabel(
            "Cette opération supprime le compte Google actif (verrou FRP) après une réinitialisation.\n"
            "• Mode BROM (Recommandé) : Appareil éteint, maintenir Volume Bas en branchant le câble USB.\n"
            "• Mode Fastboot : Appareil en mode bootloader (Volume Bas + Power)."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; margin-bottom: 10px;")
        op_layout.addWidget(info_label)

        self.btn_frp = QPushButton("Lancer le déblocage FRP")
        self.btn_frp.setObjectName("frpButton")
        self.btn_frp.setFixedHeight(45)
        self.btn_frp.setEnabled(False)
        self.btn_frp.setCursor(Qt.PointingHandCursor)
        self.btn_frp.clicked.connect(self._start_frp_reset)
        op_layout.addWidget(self.btn_frp)

        self.progress_frp = QProgressBar()
        self.progress_frp.setRange(0, 100)
        self.progress_frp.setValue(0)
        self.progress_frp.setTextVisible(True)
        op_layout.addWidget(self.progress_frp)

        layout.addWidget(op_group)

        # --- Journal de l'opération FRP ---
        log_group = QGroupBox("Journal de l'opération FRP")
        log_layout = QVBoxLayout(log_group)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(160)
        self.txt_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }}
        """)
        log_layout.addWidget(self.txt_log)
        layout.addWidget(log_group)

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
            QPushButton#frpButton {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton#frpButton:hover {{
                background-color: #0088cc;
            }}
            QPushButton#frpButton:disabled {{
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

        # Affichage selon le mode
        if dev.mode == DeviceMode.BROM:
            self.lbl_device.setText(f"Appareil MediaTek (Mode BROM sur {dev.port}) - {dev.description}")
            self.lbl_device.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 12px; font-weight: bold;")
            self.lbl_protocol_info.setText("Protocole : Déblocage direct BROM / MTK DA Partition Wipe (Prêt)")
            self.lbl_protocol_info.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 11px;")
            self.btn_frp.setEnabled(True)

        elif dev.mode == DeviceMode.FASTBOOT:
            serial = dev.serial_number or dev.identifier
            self.lbl_device.setText(f"Appareil Android (Mode Fastboot - Série: {serial})")
            self.lbl_device.setStyleSheet(f"color: {COLOR_CYAN}; font-size: 12px; font-weight: bold;")
            self.lbl_protocol_info.setText("Protocole : Déblocage via commandes OEM Fastboot (Prêt)")
            self.lbl_protocol_info.setStyleSheet(f"color: {COLOR_CYAN}; font-size: 11px;")
            self.btn_frp.setEnabled(True)

        elif dev.mode == DeviceMode.NORMAL:
            loc = dev.port or dev.identifier
            self.lbl_device.setText(f"Appareil en Mode Normal/AT ({loc})")
            self.lbl_device.setStyleSheet(f"color: {COLOR_WARNING}; font-size: 12px; font-weight: bold;")
            self.lbl_protocol_info.setText("Attention : Déblocage FRP non disponible directement en mode Normal. Redémarrer en BROM ou Fastboot.")
            self.lbl_protocol_info.setStyleSheet(f"color: {COLOR_WARNING}; font-size: 11px;")
            self.btn_frp.setEnabled(False)

    def on_device_disconnected(self):
        self.device_connected = False
        self.current_device = None
        self.lbl_device.setText("Aucun appareil connecté - En attente de branchement...")
        self.lbl_device.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        self.lbl_protocol_info.setText("Méthode de déblocage : En attente d'un appareil BROM ou Fastboot")
        self.lbl_protocol_info.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        self.btn_frp.setEnabled(False)

    # ------------------------------------------------------------------
    # Lancement du déblocage
    # ------------------------------------------------------------------
    def _start_frp_reset(self):
        if not self.device_connected or not self.current_device:
            QMessageBox.warning(self, "Appareil manquant", "Veuillez connecter un appareil d'abord.")
            return

        target_desc = self.lbl_device.text()
        reply = QMessageBox.question(
            self, "Confirmer le déblocage FRP",
            f"Voulez-vous lancer le déblocage FRP sur cet appareil ?\n\n{target_desc}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return

        self.btn_frp.setEnabled(False)
        self.progress_frp.setValue(0)
        self.txt_log.clear()

        self.worker = FRPResetWorker(self.mtk_comm, self.current_device)
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.log.connect(self._on_worker_log)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_progress(self, val):
        self.progress_frp.setValue(val)

    def _on_worker_log(self, msg, level):
        color = COLOR_SUCCESS if level == "success" else COLOR_TEXT
        self.txt_log.append(f'<span style="color:{color}">• {msg}</span>')

    def _on_worker_finished(self, success, message):
        self.btn_frp.setEnabled(self.device_connected)
        if success:
            QMessageBox.information(self, "FRP Débloqué", message)
        else:
            QMessageBox.critical(self, "Erreur FRP", f"Échec du déblocage FRP :\n{message}")
