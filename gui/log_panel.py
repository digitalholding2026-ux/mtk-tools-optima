# -*- coding: utf-8 -*-
"""
Panneau de logs en temps réel pour l'application Optima MTK Tool.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

COLOR_BG_PANEL = "#161a28"
COLOR_TEXT = "#e8eaf2"
COLOR_TEXT_MUTED = "#8a92a8"
COLOR_BORDER = "#2c334a"
COLOR_SUCCESS = "#2ecc71"
COLOR_WARNING = "#f1c40f"
COLOR_ERROR = "#e74c3c"
COLOR_INFO = "#00a2ff"


class LogPanel(QWidget):
    """Panneau de logs avec horodatage et coloration par niveau."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(140)
        self.setObjectName("logPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Barre d'outils du log
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(10, 5, 10, 5)

        lbl_title = QLabel("Journaux en temps réel")
        lbl_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px; font-weight: bold;")
        toolbar.addWidget(lbl_title)
        toolbar.addStretch()

        btn_clear = QPushButton("Effacer")
        btn_clear.setFixedSize(70, 24)
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.clicked.connect(self.clear_logs)
        toolbar.addWidget(btn_clear)

        layout.addLayout(toolbar)

        # Zone de texte des logs
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0c0e16;
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 11px;
                padding: 6px;
            }}
        """)
        layout.addWidget(self.txt_log)

    def add_log(self, message, level="info"):
        """Ajoute un message au journal avec horodatage et couleur selon le niveau."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Couleur selon le niveau
        level_colors = {
            "info": COLOR_INFO,
            "success": COLOR_SUCCESS,
            "warning": COLOR_WARNING,
            "error": COLOR_ERROR,
        }
        color = level_colors.get(level, COLOR_INFO)

        # Format HTML pour coloration
        html = (
            f'<span style="color:{COLOR_TEXT_MUTED}">[{timestamp}]</span> '
            f'<span style="color:{color}; font-weight:bold">[{level.upper()}]</span> '
            f'<span style="color:{COLOR_TEXT}">{message}</span>'
        )

        self.txt_log.append(html)

        # Auto-scroll vers le bas
        scrollbar = self.txt_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_logs(self):
        """Efface tout le contenu du journal."""
        self.txt_log.clear()
