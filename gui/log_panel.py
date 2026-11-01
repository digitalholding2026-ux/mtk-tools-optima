# -*- coding: utf-8 -*-
"""
Console de logs intégrée haute lisibilité pour Optima MTK Tool.
Police à chasse fixe Consolas/Monospace, redimensionnement dynamique,
codes couleur contrastés et boutons d'action rapide.
"""

from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

COLOR_BG_PANEL     = "#101420"
COLOR_BG_CONSOLE   = "#090c13"
COLOR_TEXT_PRIMARY = "#f1f5f9"
COLOR_TEXT_MUTED   = "#94a3b8"
COLOR_BORDER       = "#232c40"
COLOR_SUCCESS      = "#34d399"  # Vert émeraude vif
COLOR_WARNING      = "#fbbf24"  # Ambre vif
COLOR_ERROR        = "#f87171"  # Rouge vif
COLOR_INFO         = "#cbd5e1"  # Blanc doux
COLOR_ACCENT       = "#38bdf8"  # Cyan ciel


class LogPanel(QWidget):
    """Console d'atelier en temps réel (layout dynamique, non bloquant)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._log_count = 0
        self.setMinimumHeight(120)
        self.setObjectName("logPanel")

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 8)
        layout.setSpacing(5)

        # ── Barre d'outils supérieure de la console ──────────────────
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(8)

        lbl_icon = QLabel("📟")
        lbl_icon.setFont(QFont("Segoe UI Emoji", 10))
        toolbar.addWidget(lbl_icon)

        self.lbl_title = QLabel("CONSOLE D'ATELIER EN TEMPS RÉEL")
        self.lbl_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.lbl_title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; letter-spacing: 0.5px;")
        toolbar.addWidget(self.lbl_title)

        self.lbl_counter = QLabel("(0 événement)")
        self.lbl_counter.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
        toolbar.addWidget(self.lbl_counter)

        toolbar.addStretch()

        # Bouton Copier
        self.btn_copy = QPushButton("📋 Copier")
        self.btn_copy.setFixedHeight(24)
        self.btn_copy.setFixedWidth(70)
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_copy.clicked.connect(self._copy_logs)
        toolbar.addWidget(self.btn_copy)

        # Bouton Effacer
        self.btn_clear = QPushButton("🗑️ Effacer")
        self.btn_clear.setFixedHeight(24)
        self.btn_clear.setFixedWidth(70)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.setFont(QFont("Segoe UI", 9, QFont.Bold))
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
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                font-family: Consolas, 'Cascadia Code', 'Courier New', monospace;
                font-size: 11px;
                padding: 4px 8px;
            }}
        """)
        layout.addWidget(self.txt_log, stretch=1)

        self.setStyleSheet(f"""
            QWidget#logPanel {{
                background-color: {COLOR_BG_PANEL};
                border-top: 1px solid {COLOR_BORDER};
            }}
            QPushButton {{
                background-color: #1a2235;
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: {COLOR_ACCENT};
                background-color: #242f49;
            }}
        """)

    def add_log(self, message: str, level: str = "info"):
        self._log_count += 1
        self.lbl_counter.setText(f"({self._log_count} événements)")

        timestamp = datetime.now().strftime("%H:%M:%S")

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
            text_color = COLOR_WARNING
            badge_txt = "AVERT  "
        else:
            badge_color = COLOR_ACCENT if message.startswith("[+]") else COLOR_TEXT_MUTED
            text_color = COLOR_TEXT_PRIMARY
            badge_txt = "INFO   "

        clean_msg = message
        for tag in ["[SUCCESS]", "[ERROR]", "[WARNING]", "[INFO]"]:
            if clean_msg.startswith(tag):
                clean_msg = clean_msg[len(tag):].strip()

        html_entry = (
            f'<div style="margin-bottom: 2px;">'
            f'<span style="color:#64748b;">[{timestamp}]</span> '
            f'<span style="color:{badge_color}; font-weight:bold;">[{badge_txt}]</span> '
            f'<span style="color:{text_color}; font-family:Consolas, monospace;">{clean_msg}</span>'
            f'</div>'
        )

        self.txt_log.append(html_entry)

        scrollbar = self.txt_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_logs(self):
        self.txt_log.clear()
        self._log_count = 0
        self.lbl_counter.setText("(0 événement)")

    def _copy_logs(self):
        plain_text = self.txt_log.toPlainText()
        if plain_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(plain_text)
            self.lbl_counter.setText(f"({self._log_count} événements — Copié !)")
