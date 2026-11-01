# -*- coding: utf-8 -*-
"""
Assistant visuel de connexion Just-In-Time (JIT) pour Optima MTK Tool.
Affiche une boîte de dialogue modale d'instructions claires lors du lancement
d'une action (Lire Infos, Factory Reset, Effacer FRP, Flash) et écoute activement
le branchement USB en arrière-plan sans figer l'interface.
"""

from typing import Optional, List, Callable
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon

from core.detector import JITConnectionWorker, ConnectedDevice, DeviceMode

COLOR_BG_DARK = "#0f111a"
COLOR_BG_PANEL = "#161a28"
COLOR_BG_CARD = "#121522"
COLOR_ACCENT = "#00a2ff"
COLOR_ACCENT_HOVER = "#0088cc"
COLOR_TEXT = "#e8eaf2"
COLOR_TEXT_MUTED = "#8a92a8"
COLOR_BORDER = "#2c334a"
COLOR_SUCCESS = "#2ecc71"
COLOR_WARNING = "#f1c40f"
COLOR_ERROR = "#e74c3c"
COLOR_CYAN = "#00c3ff"


class ConnectionAssistantDialog(QDialog):
    """
    Boîte de dialogue modale d'instructions avec animation d'attente
    et écoute active temporaire en arrière-plan (JIT).
    """

    def __init__(
        self,
        action_name: str,
        target_modes: Optional[List[DeviceMode]] = None,
        custom_instructions: Optional[str] = None,
        timeout: int = 60,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.action_name = action_name
        self.target_modes = target_modes or [DeviceMode.BROM, DeviceMode.FASTBOOT]
        self.custom_instructions = custom_instructions
        self.timeout = timeout

        self.detected_device: Optional[ConnectedDevice] = None
        self.timed_out: bool = False
        self.cancelled: bool = False
        self.worker: Optional[JITConnectionWorker] = None

        self._init_window()
        self._setup_ui()
        self._apply_stylesheet()

    def _init_window(self):
        self.setWindowTitle(f"Assistant de Connexion - {self.action_name}")
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(560, 480)
        # Supprime le bouton d'aide '?' de Windows
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 22, 25, 22)
        layout.setSpacing(16)

        # --- En-tête : Badge d'action & Titre ---
        header_layout = QVBoxLayout()
        header_layout.setSpacing(6)

        pill_container = QHBoxLayout()
        lbl_pill = QLabel(f"ACTION REQUISE : {self.action_name.upper()}")
        lbl_pill.setObjectName("actionPill")
        pill_container.addWidget(lbl_pill)
        pill_container.addStretch()
        header_layout.addLayout(pill_container)

        lbl_title = QLabel("Connexion de l'appareil requise")
        lbl_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        lbl_title.setStyleSheet(f"color: {COLOR_TEXT};")
        header_layout.addWidget(lbl_title)

        lbl_desc = QLabel("Veuillez connecter votre smartphone selon la procédure ci-dessous :")
        lbl_desc.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        header_layout.addWidget(lbl_desc)

        layout.addLayout(header_layout)

        # --- Carte d'instructions visuelles ---
        instructions_frame = QFrame()
        instructions_frame.setObjectName("instructionsFrame")
        inst_layout = QVBoxLayout(instructions_frame)
        inst_layout.setContentsMargins(18, 14, 18, 14)
        inst_layout.setSpacing(10)

        if self.custom_instructions:
            lbl_custom = QLabel(self.custom_instructions)
            lbl_custom.setWordWrap(True)
            lbl_custom.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px;")
            inst_layout.addWidget(lbl_custom)
        else:
            inst_layout.addWidget(self._create_step_row("1", "Éteignez complètement", "le smartphone et attendez 5 secondes."))
            inst_layout.addWidget(self._create_step_row("2", "Maintenez enfoncée", "la touche <b>Volume Bas</b> (ou <b>Vol- & Vol+</b> selon modèle)."))
            inst_layout.addWidget(self._create_step_row("3", "Connectez le câble USB", "au PC tout en maintenant la touche."))
            inst_layout.addWidget(self._create_step_row("4", "Relâchez la touche", "dès que le signal de détection retentit."))

        layout.addWidget(instructions_frame)

        # --- Zone d'état d'attente & Animation de chargement ---
        waiting_frame = QFrame()
        waiting_frame.setObjectName("waitingFrame")
        waiting_layout = QVBoxLayout(waiting_frame)
        waiting_layout.setContentsMargins(16, 12, 16, 12)
        waiting_layout.setSpacing(8)

        status_row = QHBoxLayout()
        self.lbl_status = QLabel("⚡ En attente de l'appareil...")
        self.lbl_status.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.lbl_status.setStyleSheet(f"color: {COLOR_CYAN};")

        self.lbl_timer = QLabel(f"Délai : {self.timeout}s")
        self.lbl_timer.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.lbl_timer.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

        status_row.addWidget(self.lbl_status)
        status_row.addStretch()
        status_row.addWidget(self.lbl_timer)
        waiting_layout.addLayout(status_row)

        # Animation de chargement continue (Marquee progress bar non bornée)
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("waitingProgressBar")
        self.progress_bar.setRange(0, 0)  # Mode indéterminé / animation continue
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        waiting_layout.addWidget(self.progress_bar)

        self.lbl_details = QLabel("Écoute active du port MediaTek VCOM (VID: 0E8D) & Fastboot en cours...")
        self.lbl_details.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-style: italic;")
        waiting_layout.addWidget(self.lbl_details)

        layout.addWidget(waiting_frame)

        # --- Bouton d'annulation ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Annuler l'opération")
        self.btn_cancel.setObjectName("cancelButton")
        self.btn_cancel.setFixedSize(170, 38)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(btn_layout)

    def _create_step_row(self, number: str, bold_text: str, normal_text: str) -> QWidget:
        """Crée une ligne d'instruction numérotée avec style soigné."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 2, 0, 2)
        row_layout.setSpacing(12)

        lbl_badge = QLabel(number)
        lbl_badge.setObjectName("stepBadge")
        lbl_badge.setFixedSize(22, 22)
        lbl_badge.setAlignment(Qt.AlignCenter)

        lbl_text = QLabel(f"<b>{bold_text}</b> {normal_text}")
        lbl_text.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 11px;")
        lbl_text.setWordWrap(True)

        row_layout.addWidget(lbl_badge)
        row_layout.addWidget(lbl_text, stretch=1)
        return row_widget

    def _apply_stylesheet(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT};
            }}
            QLabel#actionPill {{
                background-color: #00a2ff22;
                color: {COLOR_CYAN};
                border: 1px solid {COLOR_ACCENT};
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
            QFrame#instructionsFrame {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
            QLabel#stepBadge {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
                border-radius: 11px;
                font-size: 11px;
                font-weight: bold;
            }}
            QFrame#waitingFrame {{
                background-color: #0c0e16;
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
            QProgressBar#waitingProgressBar {{
                background-color: #1a1e2d;
                border: none;
                border-radius: 4px;
            }}
            QProgressBar#waitingProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00a2ff, stop:0.5 #00d2ff, stop:1 #00a2ff);
                border-radius: 4px;
            }}
            QPushButton#cancelButton {{
                background-color: #1e2332;
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton#cancelButton:hover {{
                border-color: {COLOR_ERROR};
                color: {COLOR_ERROR};
                background-color: #241920;
            }}
            QPushButton#cancelButton:pressed {{
                background-color: {COLOR_ERROR};
                color: #ffffff;
            }}
        """)

    # ------------------------------------------------------------------
    # Cycle de vie & Écoute active JIT
    # ------------------------------------------------------------------
    def showEvent(self, event):
        """Démarre le thread d'écoute active dès l'ouverture de la popup."""
        super().showEvent(event)
        self._start_listening()

    def _start_listening(self):
        """Initialise et lance le worker d'écoute active temporaire."""
        self.worker = JITConnectionWorker(
            target_modes=self.target_modes,
            timeout_seconds=self.timeout,
            poll_interval=0.25,
            parent=self
        )
        self.worker.device_found.connect(self._on_device_found)
        self.worker.timeout_reached.connect(self._on_timeout_reached)
        self.worker.tick.connect(self._on_tick)
        self.worker.start()

    def _stop_listening(self):
        """Arrête le worker d'arrière-plan."""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker = None

    def _on_device_found(self, device: ConnectedDevice):
        """Appelé dès qu'un appareil cible est branché."""
        self.detected_device = device
        self._stop_listening()
        # Ferme automatiquement la boîte de dialogue avec succès
        self.accept()

    def _on_timeout_reached(self):
        """Appelé lorsque le délai de 60s expire sans détection."""
        self.timed_out = True
        self._stop_listening()
        self.reject()

    def _on_tick(self, remaining_seconds: int):
        """Met à jour le décompte des secondes."""
        self.lbl_timer.setText(f"Délai : {remaining_seconds}s")
        if remaining_seconds <= 10:
            self.lbl_timer.setStyleSheet(f"color: {COLOR_WARNING}; font-weight: bold;")
        else:
            self.lbl_timer.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

    def _on_cancel_clicked(self):
        """L'utilisateur clique sur [Annuler]."""
        self.cancelled = True
        self._stop_listening()
        self.reject()

    def closeEvent(self, event):
        """Garantit l'arrêt du thread en cas de fermeture par la croix de fenêtre."""
        self.cancelled = True
        self._stop_listening()
        super().closeEvent(event)


# =====================================================================
# Fonction utilitaire pour exécuter une action avec l'assistant
# =====================================================================

def execute_with_assistant(
    parent: QWidget,
    action_name: str,
    operation_func: Callable[[ConnectedDevice], None],
    target_modes: Optional[List[DeviceMode]] = None,
    custom_instructions: Optional[str] = None,
    timeout: int = 60,
    log_callback: Optional[Callable[[str, str], None]] = None
) -> bool:
    """
    Exécute le workflow Just-In-Time complet :
      1. Ouvre la popup d'instruction avec animation et bouton Annuler.
      2. Surveille en arrière-plan la connexion de l'appareil.
      3. Dès détection : ferme la popup, consigne le log propre et exécute l'action.
      4. Si annulation ou timeout : ferme proprement la popup sans bloquer.
    """
    dialog = ConnectionAssistantDialog(
        action_name=action_name,
        target_modes=target_modes,
        custom_instructions=custom_instructions,
        timeout=timeout,
        parent=parent
    )

    result = dialog.exec_()

    if result == QDialog.Accepted and dialog.detected_device:
        device = dialog.detected_device
        loc = device.port or device.serial_number or device.identifier

        # Log propre requis par le cahier des charges
        msg = f"Appareil détecté sur {loc}. Exécution de {action_name}..."
        if log_callback:
            log_callback(msg, "success")

        # Exécution de la fonction métier correspondante
        operation_func(device)
        return True

    elif dialog.timed_out:
        msg = f"Délai d'attente dépassé ({timeout}s) pour '{action_name}'. Aucun appareil détecté."
        if log_callback:
            log_callback(msg, "warning")
        QMessageBox.warning(
            parent,
            "Délai de connexion dépassé",
            f"Aucun appareil n'a été détecté après {timeout} secondes.\n"
            f"L'opération '{action_name}' a été annulée."
        )
        return False

    else:
        # Annulé par l'utilisateur
        msg = f"Opération '{action_name}' annulée par l'utilisateur."
        if log_callback:
            log_callback(msg, "info")
        return False
