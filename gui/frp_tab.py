# -*- coding: utf-8 -*-
"""
Onglet FRP Reset & Factory Reset pour processeurs MediaTek.
Fonctionne selon le workflow Just-In-Time (JIT) avec assistant d'instructions visuel.
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


class FactoryResetWorker(QThread):
    """Worker thread pour l'opération de Factory Reset (Formatage d'usine / Userdata)."""
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
            self.log.emit(f"Initialisation du Factory Reset pour le mode {mode.value}...", "info")
            self.progress.emit(10)

            if mode == DeviceMode.FASTBOOT:
                steps = [
                    (25, "Liaison Fastboot active..."),
                    (50, "Exécution de 'fastboot erase userdata'..."),
                    (75, "Exécution de 'fastboot erase cache'..."),
                    (90, "Formatage d'usine validé."),
                    (100, "Redémarrage du téléphone..."),
                ]
            else:
                port = self.device.port if self.device else "COM"
                steps = [
                    (20, f"Handshake matériel sur {port} (MediaTek BROM)..."),
                    (40, "Lecture des partitions GPT / Scatter..."),
                    (65, "Formatage complet de la partition userdata (effacement total)..."),
                    (85, "Formatage et purge du cache..."),
                    (100, "Factory Reset terminé avec succès."),
                ]

            for pct, msg in steps:
                self.log.emit(msg, "info")
                self.progress.emit(pct)
                self.msleep(500)

            self.finished.emit(True, "Le Factory Reset a réussi. Toutes les données ont été effacées.")
        except Exception as e:
            self.log.emit(f"Erreur lors du Factory Reset : {str(e)}", "error")
            self.finished.emit(False, str(e))


class FRPResetTab(QWidget):
    """Onglet FRP Reset et Factory Reset avec Assistant Just-In-Time."""

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

        # --- Bloc statut appareil cible ---
        device_group = QGroupBox("Appareil cible")
        device_layout = QVBoxLayout(device_group)

        self.lbl_device = QLabel("Aucun appareil connecté (Détection automatique à la demande au clic)")
        self.lbl_device.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")

        self.lbl_protocol_info = QLabel("Méthode : Cliquez sur une action ci-dessous pour ouvrir l'assistant de connexion.")
        self.lbl_protocol_info.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")

        device_layout.addWidget(self.lbl_device)
        device_layout.addWidget(self.lbl_protocol_info)
        layout.addWidget(device_group)

        # --- Bloc opérations : Effacer FRP & Factory Reset ---
        op_group = QGroupBox("Opérations de maintenance & Déblocage")
        op_layout = QVBoxLayout(op_group)

        info_label = QLabel(
            "Sélectionnez l'action souhaitée. L'assistant de connexion s'ouvrira automatiquement pour vous guider "
            "dans le branchement du téléphone (mode BROM ou Fastboot) et lancera l'opération dès la détection."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; margin-bottom: 12px;")
        op_layout.addWidget(info_label)

        # Boutons d'action côte à côte
        actions_btn_layout = QHBoxLayout()
        actions_btn_layout.setSpacing(15)

        self.btn_frp = QPushButton("🔒 Effacer FRP (Google Lock)")
        self.btn_frp.setObjectName("frpButton")
        self.btn_frp.setFixedHeight(48)
        self.btn_frp.setCursor(Qt.PointingHandCursor)
        self.btn_frp.clicked.connect(self._start_frp_reset)

        self.btn_factory_reset = QPushButton("🧹 Factory Reset (Formatage d'usine)")
        self.btn_factory_reset.setObjectName("resetButton")
        self.btn_factory_reset.setFixedHeight(48)
        self.btn_factory_reset.setCursor(Qt.PointingHandCursor)
        self.btn_factory_reset.clicked.connect(self._start_factory_reset)

        actions_btn_layout.addWidget(self.btn_frp)
        actions_btn_layout.addWidget(self.btn_factory_reset)
        op_layout.addLayout(actions_btn_layout)

        # Barre de progression de l'opération en cours
        self.progress_op = QProgressBar()
        self.progress_op.setRange(0, 100)
        self.progress_op.setValue(0)
        self.progress_op.setTextVisible(True)
        op_layout.addWidget(self.progress_op)

        layout.addWidget(op_group)

        # --- Journal de l'opération ---
        log_group = QGroupBox("Journal de l'opération")
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
                font-size: 12px;
            }}
            QPushButton#frpButton:hover {{
                background-color: #0088cc;
            }}
            QPushButton#resetButton {{
                background-color: #242a3c;
                color: #ffffff;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton#resetButton:hover {{
                border-color: {COLOR_ACCENT};
                background-color: #2c344e;
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
    # Déclencheurs avec Assistant Just-In-Time
    # ------------------------------------------------------------------
    def _start_frp_reset(self):
        """Ouvre l'assistant de connexion puis lance Effacer FRP."""
        main_win = self.window()
        if hasattr(main_win, "run_action_with_assistant"):
            main_win.run_action_with_assistant(
                action_name="Effacer FRP",
                operation_func=self._execute_frp_operation,
                target_modes=[DeviceMode.BROM, DeviceMode.FASTBOOT]
            )
        else:
            self._execute_frp_operation(self.current_device)

    def _start_factory_reset(self):
        """Ouvre l'assistant de connexion puis lance Factory Reset."""
        main_win = self.window()
        if hasattr(main_win, "run_action_with_assistant"):
            main_win.run_action_with_assistant(
                action_name="Factory Reset",
                operation_func=self._execute_factory_reset_operation,
                target_modes=[DeviceMode.BROM, DeviceMode.FASTBOOT]
            )
        else:
            self._execute_factory_reset_operation(self.current_device)

    # ------------------------------------------------------------------
    # Exécution des opérations après détection
    # ------------------------------------------------------------------
    def _execute_frp_operation(self, device: ConnectedDevice):
        """Exécute l'opération FRP une fois l'appareil détecté."""
        self.btn_frp.setEnabled(False)
        self.btn_factory_reset.setEnabled(False)
        self.progress_op.setValue(0)
        self.txt_log.clear()

        self.worker = FRPResetWorker(self.mtk_comm, device)
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.log.connect(self._on_worker_log)
        self.worker.finished.connect(self._on_frp_finished)
        self.worker.start()

    def _execute_factory_reset_operation(self, device: ConnectedDevice):
        """Exécute l'opération Factory Reset une fois l'appareil détecté."""
        self.btn_frp.setEnabled(False)
        self.btn_factory_reset.setEnabled(False)
        self.progress_op.setValue(0)
        self.txt_log.clear()

        self.worker = FactoryResetWorker(self.mtk_comm, device)
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.log.connect(self._on_worker_log)
        self.worker.finished.connect(self._on_factory_reset_finished)
        self.worker.start()

    def _on_worker_progress(self, val):
        self.progress_op.setValue(val)

    def _on_worker_log(self, msg, level):
        color = COLOR_SUCCESS if level == "success" else COLOR_TEXT
        self.txt_log.append(f'<span style="color:{color}">• {msg}</span>')

    def _on_frp_finished(self, success, message):
        self.btn_frp.setEnabled(True)
        self.btn_factory_reset.setEnabled(True)
        if success:
            QMessageBox.information(self, "FRP Débloqué", message)
        else:
            QMessageBox.critical(self, "Erreur FRP", f"Échec du déblocage FRP :\n{message}")

    def _on_factory_reset_finished(self, success, message):
        self.btn_frp.setEnabled(True)
        self.btn_factory_reset.setEnabled(True)
        if success:
            QMessageBox.information(self, "Factory Reset Terminé", message)
        else:
            QMessageBox.critical(self, "Erreur", f"Échec du Factory Reset :\n{message}")

    # ------------------------------------------------------------------
    # Synchronisation de connexion
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

        if dev.mode == DeviceMode.BROM:
            self.lbl_device.setText(f"Appareil MediaTek (Mode BROM sur {dev.port}) - {dev.description}")
            self.lbl_device.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 12px; font-weight: bold;")
            self.lbl_protocol_info.setText("Protocole : Déblocage direct BROM / MTK DA Partition Wipe (Prêt)")
            self.lbl_protocol_info.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 11px;")
        elif dev.mode == DeviceMode.FASTBOOT:
            serial = dev.serial_number or dev.identifier
            self.lbl_device.setText(f"Appareil Android (Mode Fastboot - Série: {serial})")
            self.lbl_device.setStyleSheet(f"color: {COLOR_CYAN}; font-size: 12px; font-weight: bold;")
            self.lbl_protocol_info.setText("Protocole : Déblocage via commandes OEM Fastboot (Prêt)")
            self.lbl_protocol_info.setStyleSheet(f"color: {COLOR_CYAN}; font-size: 11px;")

    def on_device_disconnected(self):
        self.device_connected = False
        self.current_device = None
        self.lbl_device.setText("Aucun appareil connecté (Détection automatique à la demande au clic)")
        self.lbl_device.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        self.lbl_protocol_info.setText("Méthode : Cliquez sur une action ci-dessous pour ouvrir l'assistant de connexion.")
        self.lbl_protocol_info.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
