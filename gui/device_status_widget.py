# -*- coding: utf-8 -*-
"""
Widget de statut de connexion persistant pour Optima MTK Tool.
Affiche en permanence l'état de l'appareil connecté entre l'en-tête et les onglets,
avec 4 états visuels distincts (rouge / vert) et animation LED au repos.
"""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont


# =====================================================================
# Palette de couleurs (doit rester synchrone avec main_window.py)
# =====================================================================
COLOR_BG_DARK       = "#0f111a"    # Fond général très sombre
COLOR_BG_PANEL      = "#161a28"    # Fond des panneaux
COLOR_TEXT          = "#e8eaf2"    # Texte principal
COLOR_TEXT_MUTED    = "#8a92a8"    # Texte secondaire
COLOR_BORDER        = "#2c334a"    # Bordures neutres
COLOR_SUCCESS       = "#2ecc71"    # Vert succès (connecté)
COLOR_ERROR         = "#e74c3c"    # Rouge erreur (aucun appareil)
COLOR_ERROR_DARK    = "#7f1f1f"    # Rouge sombre (clignotement LED)
COLOR_CONNECTED_BG  = "#0b1a0e"    # Fond teinte verte (appareil présent)


class DeviceStatusBanner(QFrame):
    """
    Bandeau de statut fixe (48 px de haut) inséré entre l'en-tête et les onglets.

    États affichés :
        🔴  Aucun appareil détecté          — fond sombre, LED rouge clignotante
        🟢  Appareil détecté en mode Normal / ADB     — fond vert sombre, LED verte
        🟢  Appareil détecté en mode Fastboot         — fond vert sombre, LED verte
        🟢  Appareil détecté en mode BROM / Preloader (Port COM...) — idem
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("deviceStatusBanner")
        self.setFixedHeight(48)

        self._connected = False          # État courant
        self._led_bright = True          # Alternance de l'animation LED rouge

        self._build_ui()
        self._apply_stylesheet_none()

        # ── Animation de clignotement de la LED (quand aucun appareil) ──
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(800)          # 800 ms par alternance
        self._blink_timer.timeout.connect(self._blink_led)
        self._blink_timer.start()                   # Démarre dès la création

    # ------------------------------------------------------------------
    # Construction de l'interface interne
    # ------------------------------------------------------------------
    def _build_ui(self):
        """Construit la disposition interne : LED + texte titre + sous-texte."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(14)

        # ── Indicateur LED ──────────────────────────────────────────────
        self.lbl_led = QLabel("●")
        self.lbl_led.setObjectName("bannerLed")
        self.lbl_led.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.lbl_led.setFixedWidth(26)
        self.lbl_led.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_led)

        # ── Bloc texte (titre + sous-titre) ─────────────────────────────
        text_block = QVBoxLayout()
        text_block.setContentsMargins(0, 0, 0, 0)
        text_block.setSpacing(1)

        self.lbl_status = QLabel("🔴 Aucun appareil détecté")
        self.lbl_status.setObjectName("bannerStatus")
        self.lbl_status.setFont(QFont("Segoe UI", 13, QFont.Bold))

        self.lbl_detail = QLabel("Surveillance active (BROM, Fastboot, ADB)…")
        self.lbl_detail.setObjectName("bannerDetail")
        self.lbl_detail.setFont(QFont("Segoe UI", 9))

        text_block.addWidget(self.lbl_status)
        text_block.addWidget(self.lbl_detail)
        layout.addLayout(text_block)
        layout.addStretch()

    # ------------------------------------------------------------------
    # Slot public de mise à jour (branché sur detector.status_updated)
    # ------------------------------------------------------------------
    @pyqtSlot(str, str, str, str)
    def update_status(self, mode_str: str, title: str, subtitle: str, color: str):
        """
        Met à jour l'affichage complet du bandeau.

        Paramètres (même signature que _on_status_updated de MainWindow) :
            mode_str  : "NONE" | "BROM" | "FASTBOOT" | "NORMAL"
            title     : texte principal (ex: "🟢 Appareil détecté en mode Fastboot")
            subtitle  : texte secondaire (protocole / VID:PID / port)
            color     : couleur hex dominant (#e74c3c rouge | #2ecc71 vert)
        """
        self._connected = (mode_str != "NONE")

        # Titre avec emoji intégré si absent
        display_title = title
        if self._connected and not display_title.startswith("🟢"):
            display_title = f"🟢 {title}"
        elif not self._connected and not display_title.startswith("🔴"):
            display_title = f"🔴 {title}"

        self.lbl_status.setText(display_title)
        self.lbl_detail.setText(subtitle)

        if self._connected:
            # ── État connecté ────────────────────────────────────────────
            self._blink_timer.stop()
            self.lbl_led.setStyleSheet(f"color: {COLOR_SUCCESS};")
            self.lbl_status.setStyleSheet(f"color: {COLOR_SUCCESS}; font-weight: bold;")
            self.lbl_detail.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
            self._apply_stylesheet_connected()
        else:
            # ── État déconnecté (animation clignotante) ──────────────────
            self.lbl_led.setStyleSheet(f"color: {COLOR_ERROR};")
            self.lbl_status.setStyleSheet(f"color: {COLOR_ERROR}; font-weight: bold;")
            self.lbl_detail.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
            self._apply_stylesheet_none()
            if not self._blink_timer.isActive():
                self._blink_timer.start()

    # ------------------------------------------------------------------
    # Animation LED rouge clignotante (aucun appareil connecté)
    # ------------------------------------------------------------------
    def _blink_led(self):
        """Alterne la couleur de la LED entre rouge vif et rouge sombre."""
        if self._connected:
            self._blink_timer.stop()
            return
        color = COLOR_ERROR if self._led_bright else COLOR_ERROR_DARK
        self.lbl_led.setStyleSheet(f"color: {color};")
        self._led_bright = not self._led_bright

    # ------------------------------------------------------------------
    # Feuilles de style par état
    # ------------------------------------------------------------------
    def _apply_stylesheet_none(self):
        """Applique le style 'aucun appareil' : fond sombre, bordure rouge."""
        self.setStyleSheet(f"""
            QFrame#deviceStatusBanner {{
                background-color: {COLOR_BG_PANEL};
                border-bottom: 2px solid {COLOR_ERROR}88;
            }}
            QLabel#bannerStatus {{
                color: {COLOR_ERROR};
                font-size: 13px;
                font-weight: bold;
                background: transparent;
            }}
            QLabel#bannerDetail {{
                color: {COLOR_TEXT_MUTED};
                font-size: 9px;
                background: transparent;
            }}
        """)

    def _apply_stylesheet_connected(self):
        """Applique le style 'appareil connecté' : fond vert sombre, bordure verte."""
        self.setStyleSheet(f"""
            QFrame#deviceStatusBanner {{
                background-color: {COLOR_CONNECTED_BG};
                border-bottom: 2px solid {COLOR_SUCCESS}88;
            }}
            QLabel#bannerStatus {{
                color: {COLOR_SUCCESS};
                font-size: 13px;
                font-weight: bold;
                background: transparent;
            }}
            QLabel#bannerDetail {{
                color: {COLOR_TEXT_MUTED};
                font-size: 9px;
                background: transparent;
            }}
        """)
