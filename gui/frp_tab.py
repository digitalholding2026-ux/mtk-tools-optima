# -*- coding: utf-8 -*-
"""
Onglet FRP Reset - Déblocage FRP (Factory Reset Protection) pour MediaTek.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QTextEdit, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

COLOR_BG_TAB = "#1e2332"
COLOR_BG_PANEL = "#161a28"
COLOR_ACCENT = "#00a2ff"
COLOR_TEXT = "#e8eaf2"
COLOR_TEXT_MUTED = "#8a92a8"
COLOR_BORDER = "#2c334a"
COLOR_SUCCESS = "#2ecc71"
COLOR_WARNING = "#f1c40f"
COLOR_ERROR = "#e74c3c"


class FRPResetWorker(QThread):
    """Worker thread pour l'opération de déblocage FRP (non bloquant)."""
    progress = pyqtSignal(int)
    log = pyqtSignal(str, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, mtk_comm, port):
        super().__init__()
        self.mtk_comm = mtk_comm
        self.port = port

    def run(self):
        try:
            self.log.emit("Démarrage du déblocage FRP...", "info")
            self.progress.emit(10)

            # Simulation des étapes de déblocage FRP
            steps = [
                (20, "Connexion à l'appareil en mode BROM..."),
                (40, "Lecture de la partition FRP..."),
                (60, "Effacement des données FRP (frp, frpbackup)..."),
                (80, "Redémarrage du chargeur d'amorçage..."),
                (100, "Déblocage FRP terminé."),
            ]
            for pct, msg in steps:
                self.log.emit(msg, "info")
                self.progress.emit(pct)
                self.msleep(600)

            self.finished.emit(True, "Le déblocage FRP a réussi. L'appareil redémarre sans compte Google.")
        except Exception as e:
            self.log.emit(f"Erreur lors du déblocage FRP : {str(e)}", "error")
            self.finished.emit(False, str(e))


class FRPResetTab(QWidget):
    """Onglet FRP Reset."""

    def __init__(self, mtk_comm, parent=None):
        super().__init__(parent)
        self.mtk_comm = mtk_comm
        self.device_connected = False
        self.current_port = None
        self.worker = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # --- Bloc appareil ---
        device_group = QGroupBox("Appareil cible")
        device_layout = QVBoxLayout(device_group)
        self.lbl_device = QLabel("Aucun appareil connecté")
        self.lbl_device.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        device_layout.addWidget(self.lbl_device)
        layout.addWidget(device_group)

        # --- Bloc opération FRP ---
        op_group = QGroupBox("Déblocage FRP (Factory Reset Protection)")
        op_layout = QVBoxLayout(op_group)

        info_label = QLabel(
            "Cette opération supprime le verrou FRP (compte Google précédent) "
            "après une réinitialisation d'usine. L'appareil doit être en mode "
            "BROM / préloader (appareil éteint, boutons Volume selon modèle)."
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

        # --- Bloc logs dédié (optionnel, résumé) ---
        log_group = QGroupBox("Journal de l'opération FRP")
        log_layout = QVBoxLayout(log_group)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(150)
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
    def on_device_connected(self, port, info):
        self.device_connected = True
        self.current_port = port
        self.lbl_device.setText(f"{port} - {info}")
        self.lbl_device.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 12px; font-weight: bold;")
        self.btn_frp.setEnabled(True)

    def on_device_disconnected(self):
        self.device_connected = False
        self.current_port = None
        self.lbl_device.setText("Aucun appareil connecté")
        self.lbl_device.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        self.btn_frp.setEnabled(False)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _start_frp_reset(self):
        if not self.device_connected or not self.current_port:
            QMessageBox.warning(self, "Appareil manquant", "Veuillez connecter un appareil MediaTek d'abord.")
            return

        reply = QMessageBox.question(
            self, "Confirmer le déblocage FRP",
            "Cette opération va effacer les données de protection FRP (compte Google).\n"
            "Assurez-vous que l'appareil est en mode BROM (éteint, boutons de volume selon modèle).\n\n"
            "Voulez-vous continuer ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.btn_frp.setEnabled(False)
        self.progress_frp.setValue(0)
        self.txt_log.clear()

        self.worker = FRPResetWorker(self.mtk_comm, self.current_port)
        self.worker.log.connect(self._on_worker_log)
        self.worker.progress.connect(self.progress_frp.setValue)
        self.worker.finished.connect(self._on_frp_finished)
        self.worker.start()

    def _on_worker_log(self, message, level):
        self.txt_log.append(f"[{level.upper()}] {message}")

    def _on_frp_finished(self, success, message):
        self.progress_frp.setValue(100 if success else 0)
        self.btn_frp.setEnabled(self.device_connected)
        if success:
            QMessageBox.information(self, "Succès", message)
        else:
            QMessageBox.critical(self, "Échec", message)
