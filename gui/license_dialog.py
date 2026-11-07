# -*- coding: utf-8 -*-
"""
gui/license_dialog.py — Fenêtre d'activation de licence offline Optima MTK Tool.
Affiche une boîte modale permettant de saisir un token d'activation parmi les
5 tokens valides. En cas de succès, la licence est enregistrée (license.json).
"""

from typing import Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from core.license_manager import LicenseManager, VALID_TOKENS, LICENSE_DURATION_DAYS

COLOR_BG_PANEL = "#161a28"
COLOR_BG_CARD  = "#121522"
COLOR_ACCENT   = "#00a2ff"
COLOR_TEXT     = "#e8eaf2"
COLOR_TEXT_MUT = "#94a3b8"
COLOR_BORDER   = "#252c40"
COLOR_SUCCESS  = "#2ecc71"
COLOR_ERROR    = "#e74c3c"
COLOR_WARNING  = "#f1c40f"


class LicenseDialog(QDialog):
    """
    Boîte de dialogue d'activation de licence.
    S'affiche au démarrage si aucune licence valide n'est détectée.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.license_mgr = LicenseManager()
        self.activated = False

        self.setWindowTitle("Activation de licence — Optima MTK Tool")
        self.setWindowModality(Qt.ApplicationModal)
        self.setFixedSize(560, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._setup_ui()
        self._apply_stylesheet()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(18)

        # ── En-tête ──
        header = QVBoxLayout()
        header.setSpacing(8)

        lbl_title = QLabel("LICENCE REQUISE")
        lbl_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl_title.setStyleSheet(f"color: {COLOR_ACCENT}; letter-spacing: 1px;")
        header.addWidget(lbl_title)

        lbl_sub = QLabel(
            "Optima MTK Tool nécessite une licence valide pour fonctionner. "
            "Veuillez saisir un token d'activation parmi les 5 tokens autorisés."
        )
        lbl_sub.setWordWrap(True)
        lbl_sub.setStyleSheet(f"color: {COLOR_TEXT_MUT}; font-size: 12px;")
        header.addWidget(lbl_sub)

        layout.addLayout(header)

        # ── Carte de saisie du token ──
        card = QFrame()
        card.setObjectName("licenseCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 18, 22, 18)
        card_layout.setSpacing(12)

        lbl_tok = QLabel("Token d'activation :")
        lbl_tok.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_tok.setStyleSheet(f"color: {COLOR_TEXT};")
        card_layout.addWidget(lbl_tok)

        self.txt_token = QLineEdit()
        self.txt_token.setPlaceholderText("Ex: OPTIMA-14D-A1B2")
        self.txt_token.setFixedHeight(38)
        self.txt_token.setFont(QFont("Consolas", 11, QFont.Bold))
        self.txt_token.setStyleSheet(f"""
            QLineEdit {{
                background-color: #0f1422;
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding-left: 12px;
                font-size: 12px;
            }}
            QLineEdit:focus {{
                border-color: {COLOR_ACCENT};
            }}
        """)
        self.txt_token.returnPressed.connect(self._on_activate_clicked)
        card_layout.addWidget(self.txt_token)

        # Liste des tokens valides (aide-mémoire)
        tokens_str = "  •  ".join(VALID_TOKENS)
        lbl_tokens = QLabel(f"Tokens valides : {tokens_str}")
        lbl_tokens.setWordWrap(True)
        lbl_tokens.setStyleSheet(f"color: {COLOR_TEXT_MUT}; font-size: 10px; font-style: italic;")
        card_layout.addWidget(lbl_tokens)

        self.btn_activate = QPushButton("Activer la licence")
        self.btn_activate.setObjectName("btnActivate")
        self.btn_activate.setFixedHeight(40)
        self.btn_activate.setCursor(Qt.PointingHandCursor)
        self.btn_activate.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_activate.clicked.connect(self._on_activate_clicked)
        card_layout.addWidget(self.btn_activate)

        layout.addWidget(card)

        # ── Infos durée ──
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #0b0f19;
                border: 1px solid {COLOR_BORDER};
                border-left: 4px solid {COLOR_ACCENT};
                border-radius: 6px;
            }}
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 12, 16, 12)

        lbl_info = QLabel(
            f"• Durée de validité : {LICENSE_DURATION_DAYS} jours après activation.<br>"
            "• La licence est stockée localement (license.json).<br>"
            "• Un compte à rebours s'affiche en permanence dans l'interface."
        )
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet(f"color: {COLOR_TEXT_MUT}; font-size: 11px;")
        info_layout.addWidget(lbl_info)

        layout.addWidget(info_frame)
        layout.addStretch()

        # ── Pied de page ──
        footer = QHBoxLayout()
        lbl_footer = QLabel("Optima Telecom — Atelier MTK")
        lbl_footer.setStyleSheet(f"color: {COLOR_TEXT_MUT}; font-size: 9px;")
        footer.addWidget(lbl_footer)
        footer.addStretch()
        layout.addLayout(footer)

    def _apply_stylesheet(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT};
            }}
            QFrame#licenseCard {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 10px;
            }}
            QPushButton#btnActivate {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 6px;
            }}
            QPushButton#btnActivate:hover {{
                background-color: #0088cc;
            }}
            QPushButton#btnActivate:pressed {{
                background-color: #006a99;
            }}
        """)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _on_activate_clicked(self):
        token = self.txt_token.text().strip()
        if not token:
            QMessageBox.warning(self, "Token manquant", "Veuillez saisir un token d'activation.")
            return

        ok, message = self.license_mgr.activate_token(token)
        if ok:
            QMessageBox.information(self, "Licence activée", message)
            self.activated = True
            self.accept()
        else:
            QMessageBox.critical(self, "Échec d'activation", message)
            self.txt_token.clear()
            self.txt_token.setFocus()

    def exec_(self) -> int:
        """Affiche la dialog et retourne QDialog.Accepted si activation réussie."""
        return super().exec_()
