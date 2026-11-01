# -*- coding: utf-8 -*-
"""
Panneau de console de logs intégrée pour Optima MTK Tool.
Police à chasse fixe Consolas/Monospace, horodatage et coloration syntaxique en direct :
  - 🟢 Vert pour les succès
  - 🔴 Rouge pour les erreurs
  - 🟡 Jaune pour les avertissements
  - ⚪ Blanc/Gris pour les informations standard
  - 🔵 Bleu pour les actions système
Boutons ergonomiques pour effacer et copier le journal.
"""

from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Palette de couleurs Optima Telecom
COLOR_BG_PANEL = "#121522"
COLOR_BG_CONSOLE = "#0b0d14"
COLOR_TEXT = "#e8eaf2"
COLOR_TEXT_MUTED = "#8a92a8"
COLOR_BORDER = "#252c40"
COLOR_SUCCESS = "#2ecc71"
COLOR_WARNING = "#f1c40f"
COLOR_ERROR = "#e74c3c"
COLOR_INFO = "#a0a8bf"
COLOR_ACCENT = "#00a2ff"


class LogPanel(QWidget):
    """Console de logs intégrée en bas d'application pour l'atelier de maintenance."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._log_count = 0
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(145)
        self.setObjectName("logPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 6, 15, 8)
        layout.setSpacing(5)

        # ── Barre d'outils supérieure de la console ──────────────────
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(10)

        lbl_icon = QLabel("📟")
        lbl_icon.setFont(QFont("Segoe UI Emoji", 11))
        toolbar.addWidget(lbl_icon)

        self.lbl_title = QLabel("Console d'Atelier en Temps Réel")
        self.lbl_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_title.setStyleSheet(f"color: {COLOR_TEXT};")
        toolbar.addWidget(self.lbl_title)

        self.lbl_counter = QLabel("(0 événement)")
        self.lbl_counter.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
        toolbar.addWidget(self.lbl_counter)

        toolbar.addStretch()

        # Bouton Copier
        self.btn_copy = QPushButton("📋 Copier")
        self.btn_copy.setFixedHeight(24)
        self.btn_copy.setFixedWidth(75)
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.setFont(QFont("Segoe UI", 9))
        self.btn_copy.clicked.connect(self._copy_logs)
        toolbar.addWidget(self.btn_copy)

        # Bouton Effacer
        self.btn_clear = QPushButton("🗑️ Effacer")
        self.btn_clear.setFixedHeight(24)
        self.btn_clear.setFixedWidth(75)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.setFont(QFont("Segoe UI", 9))
        self.btn_clear.clicked.connect(self.clear_logs)
        toolbar.addWidget(self.btn_clear)

        layout.addLayout(toolbar)

        # ── Zone de texte (Console Monospace) ─────────────────────────
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setObjectName("consoleOutput")
        self.txt_log.setStyleSheet(f"""
            QTextEdit#consoleOutput {{
                background-color: {COLOR_BG_CONSOLE};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                font-family: Consolas, 'Cascadia Code', 'Courier New', monospace;
                font-size: 11px;
                padding: 6px 10px;
                line-height: 140%;
            }}
        """)
        layout.addWidget(self.txt_log)

        self.setStyleSheet(f"""
            QWidget#logPanel {{
                background-color: {COLOR_BG_PANEL};
                border-top: 1px solid {COLOR_BORDER};
            }}
            QPushButton {{
                background-color: #1a2032;
                color: {COLOR_TEXT_MUTED};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                color: {COLOR_TEXT};
                border-color: {COLOR_ACCENT};
                background-color: #242c44;
            }}
        """)

    def add_log(self, message: str, level: str = "info"):
        """
        Ajoute une entrée formatée et colorée dans la console.
          - 'success' : vert éclatant
          - 'error'   : rouge avertissement
          - 'warning' : jaune ambre
          - 'info'    : blanc cassé / gris doux
        """
        self._log_count += 1
        self.lbl_counter.setText(f"({self._log_count} événements)")

        timestamp = datetime.now().strftime("%H:%M:%S")

        # Sélection de couleur selon la gravité
        if level == "success" or "[SUCCESS]" in message:
            badge_color = COLOR_SUCCESS
            text_color = COLOR_SUCCESS
            badge_txt = "SUCCESS"
        elif level == "error" or "[ERROR]" in message:
            badge_color = COLOR_ERROR
            text_color = COLOR_ERROR
            badge_txt = "ERREUR "
        elif level == "warning" or "[WARNING]" in message or "[!]" in message:
            badge_color = COLOR_WARNING
            text_color = "#f9e79f"
            badge_txt = "AVERT  "
        else:
            badge_color = COLOR_ACCENT if message.startswith("[+]") else COLOR_TEXT_MUTED
            text_color = COLOR_TEXT
            badge_txt = "INFO   "

        # Nettoyage des balises dupliquées si déjà présentes
        clean_msg = message
        for tag in ["[SUCCESS]", "[ERROR]", "[WARNING]", "[INFO]"]:
            if clean_msg.startswith(tag):
                clean_msg = clean_msg[len(tag):].strip()

        html_entry = (
            f'<div style="margin-bottom: 2px;">'
            f'<span style="color:#5e6882;">[{timestamp}]</span> '
            f'<span style="color:{badge_color}; font-weight:bold;">[{badge_txt}]</span> '
            f'<span style="color:{text_color};">{clean_msg}</span>'
            f'</div>'
        )

        self.txt_log.append(html_entry)

        # Défilement automatique vers le dernier événement
        scrollbar = self.txt_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_logs(self):
        """Efface tout le contenu de la console."""
        self.txt_log.clear()
        self._log_count = 0
        self.lbl_counter.setText("(0 événement)")

    def _copy_logs(self):
        """Copie le contenu textuel brut du journal dans le presse-papier."""
        plain_text = self.txt_log.toPlainText()
        if plain_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(plain_text)
            self.lbl_counter.setText(f"({self._log_count} événements — Copié !)")
