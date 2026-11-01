# -*- coding: utf-8 -*-
"""
Fenêtre principale de l'application Optima MTK Tool.
Interface graphique moderne, ultra-simple et optimisée pour l'atelier de maintenance.

Organisation :
  1. En-tête permanent avec titre & bandeau de statut temps réel (🔴 / 🟢 / 🟡)
  2. Navigation par 3 onglets principaux :
       - Onglet 1 : [Infos & Diagnostic]
       - Onglet 2 : [FRP & Sécurité]
       - Onglet 3 : [Outils & Redémarrage]
  3. Console de logs intégrée en bas (Monospace Consolas, couleurs dynamiques)
"""

from typing import Optional, List, Callable
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStatusBar, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

from gui.device_info_tab import DeviceInfoTab
from gui.frp_tab import FRPResetTab
from gui.tools_tab import ToolsTab
from gui.log_panel import LogPanel
from gui.device_status_widget import DeviceStatusBanner
from core.detector import DeviceDetector, ConnectedDevice, DeviceMode
from core.mtk_communication import MTKCommunication

# Palette de couleurs Optima Telecom (Dark Mode Professionnel)
COLOR_BG_DARK = "#0d111a"          # Fond d'application très sombre
COLOR_BG_PANEL = "#121522"         # Fond des barres et panneaux
COLOR_BG_TAB = "#0f111a"           # Fond de zone d'onglets
COLOR_ACCENT = "#00a2ff"           # Bleu électrique Optima Telecom
COLOR_ACCENT_HOVER = "#0088cc"     # Bleu survol
COLOR_TEXT = "#e8eaf2"             # Texte clair principal
COLOR_TEXT_MUTED = "#8a92a8"       # Texte secondaire estompé
COLOR_BORDER = "#252c40"           # Bordures subtiles
COLOR_SUCCESS = "#2ecc71"          # Vert succès
COLOR_WARNING = "#f1c40f"          # Jaune avertissement
COLOR_ERROR = "#e74c3c"            # Rouge erreur
COLOR_CYAN = "#00c3ff"             # Cyan Fastboot


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application Optima MTK Tool."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Optima MTK Tool — Atelier de Maintenance & Déblocage")
        self.setMinimumSize(1120, 780)
        self.resize(1220, 840)

        # Initialisation du moteur de communication et du détecteur en arrière-plan
        self.mtk_comm = MTKCommunication()
        self.detector = DeviceDetector(interval=1.5)
        self.com_detector = self.detector  # Rétrocompatibilité

        # Construction de l'interface graphique refondue
        self._setup_ui()
        self._apply_stylesheet()
        self._create_menu_bar()
        self._create_status_bar()

        # Connexion des signaux de détection automatique en temps réel
        self.detector.device_detected.connect(self._on_device_detected)
        self.detector.device_lost.connect(self._on_device_lost)
        self.detector.status_updated.connect(self._on_status_updated)
        self.detector.status_updated.connect(self.status_banner.update_status)
        self.detector.log_message.connect(self._append_log)

        # Message d'accueil professionnel dans la console
        self.log_panel.add_log("Optima MTK Tool initialisé avec succès.", "success")
        self.log_panel.add_log(
            "Service de surveillance en temps réel actif (BROM MediaTek, Fastboot, ADB).",
            "info"
        )

        # Démarrage immédiat de la surveillance en arrière-plan
        self.detector.start_monitoring()

    # ------------------------------------------------------------------
    # Construction de l'interface principale
    # ------------------------------------------------------------------
    def _setup_ui(self):
        """Assemble l'en-tête, le bandeau de statut, les 3 onglets et la console."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 1. En-tête de marque permanent ───────────────────────────
        header = self._build_header()
        main_layout.addWidget(header)

        # ── 2. Bandeau d'état permanent (🔴 / 🟢 / 🟡) ────────────────
        self.status_banner = DeviceStatusBanner()
        main_layout.addWidget(self.status_banner)

        # ── 3. Navigation par Onglets (3 Onglets Principaux) ─────────
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)

        # Onglet 1 : [Infos & Diagnostic]
        self.device_info_tab = DeviceInfoTab(self.mtk_comm)
        self.tabs.addTab(self.device_info_tab, "  📋 Infos & Diagnostic  ")

        # Onglet 2 : [FRP & Sécurité]
        self.frp_tab = FRPResetTab(self.mtk_comm)
        self.tabs.addTab(self.frp_tab, "  🔒 FRP & Sécurité  ")

        # Onglet 3 : [Outils & Redémarrage]
        self.tools_tab = ToolsTab(self.mtk_comm)
        self.tabs.addTab(self.tools_tab, "  🛠️ Outils & Redémarrage  ")

        main_layout.addWidget(self.tabs, stretch=1)

        # ── 4. Console de Logs Intégrée (Bas de fenêtre) ──────────────
        self.log_panel = LogPanel()
        main_layout.addWidget(self.log_panel)

    def _build_header(self) -> QFrame:
        """Construit l'en-tête permanent avec le titre et le bouton réanalyser."""
        header = QFrame()
        header.setFixedHeight(68)
        header.setObjectName("appHeader")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(22, 0, 22, 0)
        layout.setSpacing(16)

        # Logo / Titre de l'application
        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(2)

        lbl_app_name = QLabel("OPTIMA MTK TOOL")
        lbl_app_name.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl_app_name.setStyleSheet(f"color: {COLOR_ACCENT}; letter-spacing: 0.8px;")

        lbl_app_sub = QLabel("Atelier de Maintenance & Déblocage FRP Mobile — Processeurs MediaTek")
        lbl_app_sub.setFont(QFont("Segoe UI", 9))
        lbl_app_sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

        title_box.addWidget(lbl_app_name)
        title_box.addWidget(lbl_app_sub)
        layout.addLayout(title_box)

        layout.addStretch()

        # Bouton réanalyser immédiat (F5 / clic)
        self.btn_rescan = QPushButton("🔄 Réanalyser USB")
        self.btn_rescan.setObjectName("btnHeaderRescan")
        self.btn_rescan.setToolTip("Forcer une analyse immédiate des ports USB et Fastboot (Touche F5)")
        self.btn_rescan.setFixedHeight(34)
        self.btn_rescan.setCursor(Qt.PointingHandCursor)
        self.btn_rescan.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_rescan.clicked.connect(self._on_rescan_clicked)
        layout.addWidget(self.btn_rescan)

        return header

    # ------------------------------------------------------------------
    # Menus et barre de statut système
    # ------------------------------------------------------------------
    def _create_menu_bar(self):
        menubar = self.menuBar()

        # Menu Fichier
        menu_file = menubar.addMenu("&Fichier")
        act_exit = menu_file.addAction("Quitter")
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)

        # Menu Outils
        menu_tools = menubar.addMenu("&Outils")
        act_rescan = menu_tools.addAction("Forcer l'analyse USB (F5)")
        act_rescan.setShortcut("F5")
        act_rescan.triggered.connect(self._on_rescan_clicked)
        menu_tools.addSeparator()
        act_clear = menu_tools.addAction("Effacer la console")
        act_clear.triggered.connect(self.log_panel.clear_logs)

        # Menu Aide
        menu_help = menubar.addMenu("&Aide")
        act_about = menu_help.addAction("À propos d'Optima MTK Tool")
        act_about.triggered.connect(self._show_about)

    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.heartbeat_label = QLabel("● Surveillance active (1.5s)")
        self.heartbeat_label.setStyleSheet(f"color: {COLOR_ACCENT}; font-size: 10px; margin-right: 15px;")
        self.status_bar.addWidget(self.heartbeat_label)

        self.status_label = QLabel("Aucun appareil connecté")
        self.status_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        self.status_bar.addPermanentWidget(self.status_label)
        self.status_bar.showMessage("Prêt pour la maintenance", 3000)

    # ------------------------------------------------------------------
    # Feuilles de style globales (Dark Mode Optima Telecom)
    # ------------------------------------------------------------------
    def _apply_stylesheet(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLOR_BG_DARK};
            }}
            QFrame#appHeader {{
                background-color: {COLOR_BG_PANEL};
                border-bottom: 1px solid {COLOR_BORDER};
            }}
            QPushButton#btnHeaderRescan {{
                background-color: #1a2034;
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton#btnHeaderRescan:hover {{
                border-color: {COLOR_ACCENT};
                color: {COLOR_ACCENT};
                background-color: #202840;
            }}
            QTabWidget::pane {{
                border: none;
                background-color: {COLOR_BG_TAB};
            }}
            QTabBar {{
                background-color: {COLOR_BG_PANEL};
                border-bottom: 2px solid {COLOR_BORDER};
            }}
            QTabBar::tab {{
                background-color: transparent;
                color: {COLOR_TEXT_MUTED};
                padding: 12px 24px;
                font-size: 12px;
                font-weight: bold;
                border-bottom: 3px solid transparent;
            }}
            QTabBar::tab:selected {{
                color: {COLOR_ACCENT};
                border-bottom: 3px solid {COLOR_ACCENT};
                background-color: #161c2c;
            }}
            QTabBar::tab:hover:!selected {{
                color: {COLOR_TEXT};
                background-color: #151928;
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
                padding: 2px;
            }}
            QMenuBar::item:selected {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
                border-radius: 3px;
            }}
            QMenu {{
                background-color: {COLOR_BG_PANEL};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
            }}
            QMenu::item:selected {{
                background-color: {COLOR_ACCENT};
                color: #ffffff;
            }}
        """)

    # ------------------------------------------------------------------
    # Événements et synchronisation de détection USB
    # ------------------------------------------------------------------
    def _on_rescan_clicked(self):
        """Force une analyse immédiate sans attendre l'intervalle."""
        self._append_log("[+] Analyse immédiate des ports USB/Fastboot déclenchée...", "info")
        self.detector.scan_now()

    def _on_status_updated(self, mode_str: str, title: str, subtitle: str, color: str):
        """Forwardé automatiquement vers self.status_banner."""
        pass

    def _on_device_detected(self, device: ConnectedDevice):
        """Appelé en temps réel dès qu'un appareil est connecté."""
        # 1. Mise à jour de la logique métier
        self.mtk_comm.set_device(device)

        # 2. Construction du libellé selon la spécification atelier
        # ex: 🟢 "Connecté : Infinix Hot 11 Play [Mode BROM]"
        model_name = device.description or "Périphérique MediaTek"
        if device.details.get("product_name"):
            model_name = device.details["product_name"]

        loc = device.port or device.serial_number or device.identifier
        self.status_banner.set_device_info(
            model_name=model_name,
            mode_name=device.mode_display,
            port_name=loc
        )

        # 3. Barre de statut système
        self.status_label.setText(f"Appareil connecté : {device.mode.value} ({loc})")
        self.status_label.setStyleSheet(f"color: {device.color}; font-weight: bold;")

        # 4. Transmission dynamique aux 3 onglets
        self.device_info_tab.on_device_connected(device)
        self.frp_tab.on_device_connected(device)
        self.tools_tab.on_device_connected(device)

    def _on_device_lost(self, device: ConnectedDevice):
        """Appelé en temps réel lors du débranchement de l'appareil."""
        # 1. Mise à jour du bandeau de statut
        self.status_banner.update_status(
            "NONE",
            "🔴 Aucun appareil connecté",
            "Surveillance continue active (BROM MediaTek, Fastboot, ADB)...",
            "#e74c3c"
        )

        # 2. Réinitialisation de la logique métier
        self.mtk_comm.disconnect()

        # 3. Barre de statut
        self.status_label.setText("Aucun appareil connecté")
        self.status_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

        # 4. Transmission aux 3 onglets
        self.device_info_tab.on_device_disconnected()
        self.frp_tab.on_device_disconnected()
        self.tools_tab.on_device_disconnected()

    # ------------------------------------------------------------------
    # Exécution des actions avec Assistant Just-In-Time (JIT)
    # ------------------------------------------------------------------
    def run_action_with_assistant(
        self,
        action_name: str,
        operation_func: Callable[[ConnectedDevice], None],
        target_modes: Optional[List[DeviceMode]] = None,
        custom_instructions: Optional[str] = None,
        timeout: int = 60
    ) -> bool:
        """
        Exécute une action en s'adaptant à l'état de l'appareil :
          - Si un appareil compatible est déjà détecté par la surveillance de fond :
            exécution instantanée sans popup d'attente (zéro latence).
          - Si aucun appareil n'est présent : ouvre la boîte d'instructions JIT
            avec décompte, animation et détection à la volée.
        """
        current = self.detector.get_current_device()
        if current is not None:
            mode_ok = (target_modes is None) or (current.mode in target_modes)
            if mode_ok:
                loc = current.port or current.serial_number or current.identifier
                self._append_log(
                    f"Appareil déjà présent ({current.mode.value} — {loc}). "
                    f"Exécution immédiate de « {action_name} »...",
                    "success"
                )
                self._on_device_detected(current)
                operation_func(current)
                return True

        # Ouverture de l'assistant JIT
        from gui.connection_assistant import execute_with_assistant

        def wrapped_op(device: ConnectedDevice):
            self._on_device_detected(device)
            operation_func(device)

        return execute_with_assistant(
            parent=self,
            action_name=action_name,
            operation_func=wrapped_op,
            target_modes=target_modes,
            custom_instructions=custom_instructions,
            timeout=timeout,
            log_callback=self._append_log
        )

    def _append_log(self, message: str, level: str = "info"):
        """Consigne un événement dans la console intégrée."""
        self.log_panel.add_log(message, level)

    def _show_about(self):
        QMessageBox.about(
            self,
            "À propos — Optima MTK Tool",
            "<b>Optima MTK Tool</b> v1.0.0<br><br>"
            "Solution d'atelier pour le diagnostic, le flash et le déblocage FRP "
            "des appareils équipés de processeurs <b>MediaTek</b>.<br><br>"
            "• Détection en temps réel (BROM, Fastboot, ADB)<br>"
            "• Assistant de connexion Just-In-Time<br>"
            "• Architecture multi-threadée non bloquante<br><br>"
            "© Optima Telecom — Outil de maintenance mobile"
        )

    def closeEvent(self, event):
        """Fermeture propre avec arrêt du thread de surveillance."""
        if self.mtk_comm.is_connected():
            reply = QMessageBox.question(
                self, "Confirmation de sortie",
                "Un appareil est encore synchronisé. Voulez-vous vraiment fermer l'application ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return

        self.detector.stop_monitoring()
        event.accept()

    # ------------------------------------------------------------------
    # Propriétés de rétrocompatibilité
    # ------------------------------------------------------------------
    @property
    def dashboard_tab(self):
        """Rétrocompatibilité : redirige vers l'onglet d'informations."""
        return self.device_info_tab

    @property
    def flash_tab(self):
        """Rétrocompatibilité : redirige vers l'onglet d'outils."""
        return self.tools_tab
