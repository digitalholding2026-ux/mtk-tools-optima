# -*- coding: utf-8 -*-
"""
Fenêtre principale de l'application Optima MTK Tool.
Contient la barre de menu, les onglets principaux et le panneau de logs.
"""

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStatusBar, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from gui.dashboard import DashboardTab
from gui.frp_tab import FRPResetTab
from gui.flash_tab import FlashTab
from gui.device_info_tab import DeviceInfoTab
from gui.log_panel import LogPanel
from core.com_detector import COMDetector
from core.mtk_communication import MTKCommunication


# Palette de couleurs Optima Telecom (mode sombre professionnel)
COLOR_BG_DARK = "#0f111a"          # Fond très sombre
COLOR_BG_PANEL = "#161a28"         # Fond des panneaux
COLOR_BG_TAB = "#1e2332"           # Fond des onglets
COLOR_ACCENT = "#00a2ff"           # Bleu accent Optima Telecom
COLOR_ACCENT_HOVER = "#0088cc"     # Bleu au survol
COLOR_TEXT = "#e8eaf2"             # Texte principal
COLOR_TEXT_MUTED = "#8a92a8"       # Texte secondaire
COLOR_BORDER = "#2c334a"           # Bordures
COLOR_SUCCESS = "#2ecc71"          # Vert succès
COLOR_WARNING = "#f1c40f"          # Jaune avertissement
COLOR_ERROR = "#e74c3c"            # Rouge erreur


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Optima MTK Tool - Flash & Déblocage FRP")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)

        # Initialisation des composants core
        self.com_detector = COMDetector()
        self.mtk_comm = MTKCommunication()

        # Connexion des signaux de détection
        self.com_detector.device_detected.connect(self._on_device_detected)
        self.com_detector.device_lost.connect(self._on_device_lost)
        self.com_detector.log_message.connect(self._append_log)

        # Construction de l'interface
        self._setup_ui()
        self._apply_stylesheet()
        self._create_menu_bar()
        self._create_status_bar()

        # Log de bienvenue
        self.log_panel.add_log("Optima MTK Tool v1.0.0 initialisé.", "info")
        self.log_panel.add_log("Prêt. Cliquez sur 'Détecter le port COM/USB' pour localiser l'appareil.", "info")

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------
    def _setup_ui(self):
        """Construit l'interface principale avec onglets et panneau de logs."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- En-tête (titre + bouton détection) ---
        header = self._build_header()
        main_layout.addWidget(header)

        # --- Zone centrale avec onglets ---
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)

        # Onglet Accueil / Dashboard
        self.dashboard_tab = DashboardTab(self.com_detector, self.mtk_comm)
        self.tabs.addTab(self.dashboard_tab, "Accueil")

        # Onglet FRP Reset
        self.frp_tab = FRPResetTab(self.mtk_comm)
        self.tabs.addTab(self.frp_tab, "FRP Reset")

        # Onglet Flash Tool
        self.flash_tab = FlashTab(self.mtk_comm)
        self.tabs.addTab(self.flash_tab, "Flash Tool")

        # Onglet Informations Appareil
        self.device_info_tab = DeviceInfoTab(self.mtk_comm)
        self.tabs.addTab(self.device_info_tab, "Informations Appareil")

        main_layout.addWidget(self.tabs, stretch=1)

        # --- Panneau de logs (bas) ---
        self.log_panel = LogPanel()
        main_layout.addWidget(self.log_panel)

    def _build_header(self):
        """Construit l'en-tête avec le logo/titre et le bouton de détection COM."""
        header = QFrame()
        header.setFixedHeight(70)
        header.setObjectName("header")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        # Titre
        title_label = QLabel("Optima MTK Tool")
        title_label.setObjectName("titleLabel")
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        title_label.setFont(title_font)

        subtitle_label = QLabel("Flash & Déblocage FRP - MediaTek")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_font = QFont("Segoe UI", 10)
        subtitle_label.setFont(subtitle_font)

        title_container = QVBoxLayout()
        title_container.setContentsMargins(0, 0, 0, 0)
        title_container.setSpacing(2)
        title_container.addWidget(title_label)
        title_container.addWidget(subtitle_label)

        layout.addLayout(title_container)
        layout.addStretch()

        # Bouton de détection du port COM / USB
        self.btn_detect = QPushButton("Détecter le port COM / USB")
        self.btn_detect.setObjectName("detectButton")
        self.btn_detect.setFixedSize(220, 36)
        self.btn_detect.setCursor(Qt.PointingHandCursor)
        self.btn_detect.clicked.connect(self._on_detect_clicked)
        layout.addWidget(self.btn_detect)

        return header

    def _create_menu_bar(self):
        """Crée la barre de menu de l'application."""
        menubar = self.menuBar()

        # Menu Fichier
        menu_file = menubar.addMenu("&Fichier")
        action_exit = menu_file.addAction("Quitter")
        action_exit.setShortcut("Ctrl+Q")
        action_exit.triggered.connect(self.close)

        # Menu Outils
        menu_tools = menubar.addMenu("&Outils")
        action_detect = menu_tools.addAction("Détecter les ports COM")
        action_detect.triggered.connect(self._on_detect_clicked)
        menu_tools.addSeparator()
        action_clear_logs = menu_tools.addAction("Effacer les logs")
        action_clear_logs.triggered.connect(self.log_panel.clear_logs)

        # Menu Aide
        menu_help = menubar.addMenu("&Aide")
        action_about = menu_help.addAction("À propos")
        action_about.triggered.connect(self._show_about)

    def _create_status_bar(self):
        """Crée la barre de statut en bas de fenêtre."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Aucun appareil connecté")
        self.status_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        self.status_bar.addPermanentWidget(self.status_label)
        self.status_bar.showMessage("Prêt", 3000)

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------
    def _apply_stylesheet(self):
        """Applique la feuille de style sombre Optima Telecom."""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLOR_BG_DARK};
            }}
            QFrame#header {{
                background-color: {COLOR_BG_PANEL};
                border-bottom: 1px solid {COLOR_BORDER};
            }}
            QLabel#titleLabel {{
                color: {COLOR_TEXT};
                font-size: 18px;
                font-weight: bold;
            }}
            QLabel#subtitleLabel {{
                color: {COLOR_TEXT_MUTED};
                font-size: 10px;
            }}
            QPushButton#detectButton {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton#detectButton:hover {{
                background-color: {COLOR_ACCENT_HOVER};
            }}
            QPushButton#detectButton:pressed {{
                background-color: #006fa3;
            }}
            QTabWidget::pane {{
                border: 1px solid {COLOR_BORDER};
                background-color: {COLOR_BG_TAB};
            }}
            QTabBar::tab {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT_MUTED};
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLOR_BG_TAB};
                color: {COLOR_ACCENT};
                font-weight: bold;
                border-bottom: 2px solid {COLOR_ACCENT};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: #242a3c;
                color: {COLOR_TEXT};
            }}
            QStatusBar {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT_MUTED};
                border-top: 1px solid {COLOR_BORDER};
            }}
            QMenuBar {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT};
                border-bottom: 1px solid {COLOR_BORDER};
            }}
            QMenuBar::item:selected {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
            }}
            QMenu {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
            }}
            QMenu::item:selected {{
                background-color: {COLOR_ACCENT};
            }}
        """)

    # ------------------------------------------------------------------
    # Événements / Slots
    # ------------------------------------------------------------------
    def _on_detect_clicked(self):
        """Lance la détection des ports COM / USB."""
        self.log_panel.add_log("Recherche des ports COM / USB...", "info")
        self.btn_detect.setEnabled(False)
        self.btn_detect.setText("Recherche en cours...")
        self.com_detector.scan_ports()

    def _on_device_detected(self, port, info):
        """Appelé lorsqu'un appareil MediaTek est détecté."""
        self.btn_detect.setEnabled(True)
        self.btn_detect.setText("Détecter le port COM / USB")
        self.status_label.setText(f"Appareil détecté : {port}")
        self.status_label.setStyleSheet(f"color: {COLOR_SUCCESS};")
        self.log_panel.add_log(f"Appareil MediaTek détecté sur {port} - {info}", "success")
        self.dashboard_tab.on_device_connected(port, info)
        self.device_info_tab.on_device_connected(port, info)
        self.frp_tab.on_device_connected(port, info)
        self.flash_tab.on_device_connected(port, info)

    def _on_device_lost(self, port):
        """Appelé lorsque l'appareil est déconnecté."""
        self.status_label.setText("Aucun appareil connecté")
        self.status_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")
        self.log_panel.add_log(f"Appareil déconnecté ({port})", "warning")
        self.dashboard_tab.on_device_disconnected()
        self.device_info_tab.on_device_disconnected()
        self.frp_tab.on_device_disconnected()
        self.flash_tab.on_device_disconnected()

    def _append_log(self, message, level="info"):
        """Ajoute un message au panneau de logs."""
        self.log_panel.add_log(message, level)

    def _show_about(self):
        """Affiche la boîte de dialogue À propos."""
        QMessageBox.about(
            self,
            "À propos - Optima MTK Tool",
            "<b>Optima MTK Tool</b> v1.0.0<br><br>"
            "Application de flash et déblocage FRP pour processeurs MediaTek.<br><br>"
            "© Optima Telecom - Outil de maintenance mobile<br>"
            "Mode sombre - Interface PyQt5"
        )

    def closeEvent(self, event):
        """Gestion de la fermeture de la fenêtre."""
        if self.mtk_comm.is_connected():
            reply = QMessageBox.question(
                self, "Déconnexion",
                "Un appareil est encore connecté. Voulez-vous vraiment quitter ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
        event.accept()
