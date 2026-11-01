# -*- coding: utf-8 -*-
"""
Fenêtre principale de l'application Optima MTK Tool.
Intègre la détection automatique et en temps réel des périphériques USB/COM
(Modes BROM/BootROM, Fastboot, Normal/AT).
"""

from typing import Optional, List, Callable
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
from core.detector import DeviceDetector, ConnectedDevice, DeviceMode
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
COLOR_CYAN = "#00c3ff"             # Cyan Fastboot


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Optima MTK Tool - Flash & Déblocage FRP (Auto-Détection Active)")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)

        # Initialisation du moteur de communication et du détecteur en arrière-plan
        self.mtk_comm = MTKCommunication()
        self.detector = DeviceDetector(interval=1.5)
        self.com_detector = self.detector  # Rétrocompatibilité

        # Construction de l'interface
        self._setup_ui()
        self._apply_stylesheet()
        self._create_menu_bar()
        self._create_status_bar()

        # Connexion des signaux de détection automatique
        self.detector.device_detected.connect(self._on_device_detected)
        self.detector.device_lost.connect(self._on_device_lost)
        self.detector.status_updated.connect(self._on_status_updated)
        self.detector.log_message.connect(self._append_log)

        # Message initial dans le panneau de logs
        self.log_panel.add_log("Optima MTK Tool v1.0.0 initialisé.", "info")
        self.log_panel.add_log(
            "Service de détection automatique actif en arrière-plan. "
            "Connectez un appareil en mode BROM, Fastboot ou Normal/AT.",
            "info"
        )

        # Démarrage immédiat de la surveillance en arrière-plan (QThread non bloquant)
        self.detector.start_monitoring()

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

        # --- En-tête avec titre et badge dynamique temps réel ---
        header = self._build_header()
        main_layout.addWidget(header)

        # --- Zone centrale avec onglets ---
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)

        # Onglet Accueil / Dashboard
        self.dashboard_tab = DashboardTab(self.detector, self.mtk_comm)
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
        """
        Construit l'en-tête avec le logo/titre et le Badge de Statut Dynamique
        remplaçant l'ancien bouton de détection manuelle.
        """
        header = QFrame()
        header.setFixedHeight(74)
        header.setObjectName("header")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)

        # Titre et sous-titre
        title_label = QLabel("Optima MTK Tool")
        title_label.setObjectName("titleLabel")
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        title_label.setFont(title_font)

        subtitle_label = QLabel("Flash & Déblocage FRP - MediaTek (Surveillance USB Temps Réel)")
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

        # ==============================================================
        # Badge de Statut Dynamique en Temps Réel (Remplace le bouton manuel)
        # ==============================================================
        self.status_badge_frame = QFrame()
        self.status_badge_frame.setObjectName("statusBadgeFrame")
        badge_layout = QHBoxLayout(self.status_badge_frame)
        badge_layout.setContentsMargins(14, 8, 14, 8)
        badge_layout.setSpacing(10)

        # Point indicateur LED
        self.lbl_badge_led = QLabel("●")
        self.lbl_badge_led.setObjectName("badgeLed")
        self.lbl_badge_led.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.lbl_badge_led.setStyleSheet("color: #8a92a8;")

        # Conteneur des textes du badge
        text_container = QVBoxLayout()
        text_container.setContentsMargins(0, 0, 0, 0)
        text_container.setSpacing(1)

        self.lbl_badge_title = QLabel("En attente de connexion...")
        self.lbl_badge_title.setObjectName("badgeTitle")
        self.lbl_badge_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.lbl_badge_title.setStyleSheet("color: #e8eaf2;")

        self.lbl_badge_sub = QLabel("Surveillance active (BROM, Fastboot, Normal)")
        self.lbl_badge_sub.setObjectName("badgeSubtitle")
        self.lbl_badge_sub.setFont(QFont("Segoe UI", 9))
        self.lbl_badge_sub.setStyleSheet("color: #8a92a8;")

        text_container.addWidget(self.lbl_badge_title)
        text_container.addWidget(self.lbl_badge_sub)

        # Bouton compact de réanalyse immédiate (optionnel / d'appoint)
        self.btn_rescan = QPushButton("🔄")
        self.btn_rescan.setObjectName("rescanButton")
        self.btn_rescan.setToolTip("Forcer une analyse immédiate sans attendre l'intervalle")
        self.btn_rescan.setFixedSize(32, 32)
        self.btn_rescan.setCursor(Qt.PointingHandCursor)
        self.btn_rescan.clicked.connect(self._on_rescan_clicked)

        badge_layout.addWidget(self.lbl_badge_led)
        badge_layout.addLayout(text_container)
        badge_layout.addWidget(self.btn_rescan)

        layout.addWidget(self.status_badge_frame)

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
        action_scan = menu_tools.addAction("Forcer l'analyse USB / Fastboot")
        action_scan.setShortcut("F5")
        action_scan.triggered.connect(self._on_rescan_clicked)
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

        # Indicateur de veille du service
        self.heartbeat_label = QLabel("● Surveillance active (1.5s)")
        self.heartbeat_label.setStyleSheet("color: #00a2ff; font-size: 10px; margin-right: 15px;")
        self.status_bar.addWidget(self.heartbeat_label)

        # Statut permanent de l'appareil
        self.status_label = QLabel("Aucun appareil connecté")
        self.status_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        self.status_bar.addPermanentWidget(self.status_label)
        self.status_bar.showMessage("Prêt", 3000)

    # ------------------------------------------------------------------
    # Stylesheet
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
            QFrame#statusBadgeFrame {{
                background-color: #121522;
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
            }}
            QPushButton#rescanButton {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT_MUTED};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                font-size: 13px;
            }}
            QPushButton#rescanButton:hover {{
                border-color: {COLOR_ACCENT};
                color: {COLOR_ACCENT};
                background-color: #242a3c;
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
    # Événements & Slots de Détection
    # ------------------------------------------------------------------
    def _on_rescan_clicked(self):
        """Déclenche une vérification immédiate des ports COM et Fastboot."""
        self.detector.scan_now()

    def _on_status_updated(self, mode_str, title, subtitle, color):
        """Mise à jour dynamique de l'affichage du badge d'en-tête."""
        self.lbl_badge_led.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
        self.lbl_badge_title.setText(title)
        self.lbl_badge_title.setStyleSheet(f"color: {color if mode_str != 'NONE' else '#e8eaf2'}; font-size: 11px; font-weight: bold;")
        self.lbl_badge_sub.setText(subtitle)
        self.status_badge_frame.setStyleSheet(f"""
            QFrame#statusBadgeFrame {{
                background-color: #121522;
                border: 1px solid {color}66;
                border-radius: 8px;
            }}
        """)

    def _on_device_detected(self, device: ConnectedDevice):
        """Appelé en temps réel lorsqu'un périphérique est branché/détecté."""
        # Mise à jour du badge d'en-tête
        self._on_status_updated(
            device.mode.value,
            device.badge_title,
            device.badge_subtitle,
            device.color
        )

        # 1. Mise à jour de la logique métier (protocole, port, mode)
        self.mtk_comm.set_device(device)

        # 2. Mise à jour de la barre de statut
        loc = device.port or device.serial_number or device.identifier
        self.status_label.setText(f"Appareil connecté : {device.mode.value} ({loc})")
        self.status_label.setStyleSheet(f"color: {device.color}; font-weight: bold;")

        # 3. Transmission dynamique aux onglets applicatifs
        self.dashboard_tab.on_device_connected(device)
        self.device_info_tab.on_device_connected(device)
        self.frp_tab.on_device_connected(device)
        self.flash_tab.on_device_connected(device)

    def _on_device_lost(self, device: ConnectedDevice):
        """Appelé en temps réel lorsque le périphérique est débranché."""
        # Remise à zéro du badge d'en-tête
        self._on_status_updated(
            DeviceMode.NONE.value,
            "En attente de connexion...",
            "Surveillance active (BROM, Fastboot, Normal)",
            "#8a92a8"
        )

        # 1. Mise à jour de la logique métier
        self.mtk_comm.disconnect()

        # 2. Mise à jour de la barre de statut
        self.status_label.setText("Aucun appareil connecté")
        self.status_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

        # 3. Transmission dynamique aux onglets applicatifs
        self.dashboard_tab.on_device_disconnected()
        self.device_info_tab.on_device_disconnected()
        self.frp_tab.on_device_disconnected()
        self.flash_tab.on_device_disconnected()

    def run_action_with_assistant(
        self,
        action_name: str,
        operation_func: Callable[[ConnectedDevice], None],
        target_modes: Optional[List[DeviceMode]] = None,
        custom_instructions: Optional[str] = None,
        timeout: int = 60
    ) -> bool:
        """
        Déclenche l'assistant visuel d'instructions et l'écoute active temporaire (JIT).
        Ouvre la popup, attend le branchement avec animation et décompte, ferme la popup
        dès détection, consigne le log propre et exécute operation_func.
        """
        from gui.connection_assistant import execute_with_assistant

        def wrapped_operation(device: ConnectedDevice):
            self._on_device_detected(device)
            operation_func(device)

        return execute_with_assistant(
            parent=self,
            action_name=action_name,
            operation_func=wrapped_operation,
            target_modes=target_modes,
            custom_instructions=custom_instructions,
            timeout=timeout,
            log_callback=self._append_log
        )

    def _append_log(self, message: str, level: str = "info"):
        """Ajoute un message horodaté au panneau de logs."""
        self.log_panel.add_log(message, level)

    def _show_about(self):
        """Affiche la boîte de dialogue À propos."""
        QMessageBox.about(
            self,
            "À propos - Optima MTK Tool",
            "<b>Optima MTK Tool</b> v1.0.0<br><br>"
            "Application de flash et déblocage FRP pour processeurs MediaTek.<br>"
            "Module de détection automatique en temps réel (BROM, Fastboot, Normal/AT).<br><br>"
            "© Optima Telecom - Outil de maintenance mobile<br>"
            "Mode sombre - Interface PyQt5"
        )

    def closeEvent(self, event):
        """Gestion de la fermeture de la fenêtre avec arrêt propre du thread."""
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

        # Arrêt sécurisé du thread de surveillance
        self.detector.stop_monitoring()
        event.accept()
