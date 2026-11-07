# -*- coding: utf-8 -*-
"""
gui/license_widget.py — Widget d'horloge de compte à rebours de licence Optima MTK Tool.
Affiche le temps restant de validité (ex: "Licence valide - Reste : 13j 23h 45m")
et se rafraîchit chaque seconde via QTimer. En cas d'expiration, affiche un message
d'expiration et peut ouvrir la boîte d'activation.
"""

from typing import Optional, Callable
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont

from core.license_manager import LicenseManager
from gui.license_dialog import LicenseDialog

COLOR_BG_PANEL = "#161a28"
COLOR_BG_CARD  = "#121522"
COLOR_ACCENT   = "#00a2ff"
COLOR_TEXT     = "#e8eaf2"
COLOR_TEXT_MUT = "#94a3b8"
COLOR_BORDER   = "#252c40"
COLOR_SUCCESS  = "#2ecc71"
COLOR_WARNING  = "#f1c40f"
COLOR_ERROR    = "#e74c3c"


class LicenseWidget(QWidget):
    """
    Widget affichant le compte à rebours de la licence en temps réel.
    Se rafraîchit toutes les secondes via QTimer.
    """

    license_expired = pyqtSignal()
    license_activated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_mgr = LicenseManager()
        self._on_activate_callback: Optional[Callable[[], None]] = None

        self._build_ui()
        self._apply_stylesheet()

        # Timer de rafraîchissement chaque seconde
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()

        # Première mise à jour immédiate
        self._refresh()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        self.lbl_icon = QLabel("🔐")
        self.lbl_icon.setFont(QFont("Segoe UI Emoji", 11))
        layout.addWidget(self.lbl_icon)

        self.lbl_status = QLabel("Vérification de la licence...")
        self.lbl_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.lbl_status.setStyleSheet(f"color: {COLOR_TEXT_MUT};")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        self.btn_activate = QPushButton("Activer")
        self.btn_activate.setFixedHeight(26)
        self.btn_activate.setFixedWidth(70)
        self.btn_activate.setCursor(Qt.PointingHandCursor)
        self.btn_activate.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_activate.clicked.connect(self._on_activate_clicked)
        layout.addWidget(self.btn_activate)

    def _apply_stylesheet(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
            }}
            QPushButton {{
                background-color: #1a2235;
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 9px;
            }}
            QPushButton:hover {{
                border-color: {COLOR_ACCENT};
                background-color: #242f49;
            }}
        """)

    def set_activate_callback(self, callback: Callable[[], None]):
        """Définit le callback appelé quand l'utilisateur clique sur Activer."""
        self._on_activate_callback = callback

    def _refresh(self):
        is_valid, msg, _ = self.license_mgr.is_license_valid()

        if is_valid:
            self.lbl_status.setText(msg)
            self.lbl_status.setStyleSheet(f"color: {COLOR_SUCCESS}; font-weight: bold;")
            self.lbl_icon.setText("✅")
            self.btn_activate.setVisible(False)
            self.license_expired.disconnect()
        else:
            self.lbl_status.setText(msg)
            self.lbl_status.setStyleSheet(f"color: {COLOR_ERROR}; font-weight: bold;")
            self.lbl_icon.setText("❌")
            self.btn_activate.setVisible(True)

    def _on_activate_clicked(self):
        if self._on_activate_callback:
            self._on_activate_callback()
        else:
            dlg = LicenseDialog(self)
            if dlg.exec_() == dlg.Accepted:
                self._refresh()
                self.license_activated.emit()

    def is_license_valid(self) -> bool:
        """Retourne True si la licence est valide (permet l'accès aux fonctions)."""
        is_valid, _, _ = self.license_mgr.is_license_valid()
        return is_valid
