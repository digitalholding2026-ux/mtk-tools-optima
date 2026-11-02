# -*- coding: utf-8 -*-
"""
Fenêtre principale d'Optima MTK Tool Pro.
Layouts fluides 100% dynamiques, sans cadres bloquants, avec console redimensionnable :
  1. En-tête des Marques (Top Bar compacte 44px)
  2. Bandeau de statut permanent en ligne unique (38px)
  3. Espace de travail en 3 colonnes à haute visibilité :
       - Colonne Gauche  : Liste & Filtrage des modèles/SoC
       - Colonne Centrale : Boutons d'action clairs, spacieux (min 44px)
       - Colonne Droite   : Statut matériel direct et carte de synchronisation
  4. QSplitter vertical séparant l'espace de travail et la console de logs
"""

from typing import Optional, List, Callable, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStatusBar, QMessageBox, QFrame, QSplitter, QLabel
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont

from gui.tft_widgets import (
    BrandTabBar, ModelSelectorPanel, ActionTabsPanel, ConnectionManagerPanel,
    COLOR_DARK_BG, COLOR_PANEL_BG, COLOR_BORDER, COLOR_ACCENT_BLUE,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_MUTED, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from gui.log_panel import LogPanel
from gui.device_status_widget import DeviceStatusBanner
from core.detector import DeviceDetector, ConnectedDevice, DeviceMode
from core.mtk_communication import MTKCommunication
from core.actions import (
    erase_frp, factory_reset, factory_reset_adb, read_device_info, reboot_device,
    unlock_bootloader, relock_bootloader, ActionResult
)


class MainWindow(QMainWindow):
    """Fenêtre principale professionnelle TFT Unlock Tool Pro d'Optima MTK Tool."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Optima MTK Tool Pro — Solution d'Atelier & Déverrouillage MediaTek")
        self.setMinimumSize(1100, 720)
        self.resize(1240, 820)

        # Moteur de communication & détecteur d'arrière-plan
        self.mtk_comm = MTKCommunication()
        self.detector = DeviceDetector(interval=1.5)
        self.com_detector = self.detector

        # Construction de l'interface
        self._setup_ui()
        self._apply_global_stylesheet()
        self._create_menu_bar()
        self._create_status_bar()

        # Connexions des signaux
        self.detector.device_detected.connect(self._on_device_detected)
        self.detector.device_lost.connect(self._on_device_lost)
        self.detector.status_updated.connect(self._on_status_updated)
        self.detector.log_message.connect(self._append_log)

        # Message d'accueil
        self.log_panel.add_log("Optima MTK Tool Pro initialisé avec succès.", "success")
        self.log_panel.add_log("Surveillance des liaisons matérielles en arrière-plan prête.", "info")

        # Démarrage de la surveillance
        self.detector.start_monitoring()

    # ------------------------------------------------------------------
    # Assemblage de l'interface graphique (Zéro conteneur bloquant)
    # ------------------------------------------------------------------
    def _setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── 1. En-tête des Marques (Top Bar 44px) ────────────────────
        self.brand_bar = BrandTabBar()
        self.brand_bar.brand_changed.connect(self._on_brand_changed)
        main_layout.addWidget(self.brand_bar)

        # ── 2. Bandeau d'état permanent en ligne unique (38px) ───────
        self.status_banner = DeviceStatusBanner()
        main_layout.addWidget(self.status_banner)

        # ── 3. QSplitter Vertical (Espace de travail + Console) ───────
        self.vertical_splitter = QSplitter(Qt.Vertical)
        self.vertical_splitter.setObjectName("verticalSplitter")
        self.vertical_splitter.setHandleWidth(4)

        # Espace de travail en 3 Colonnes
        workspace_frame = QFrame()
        workspace_frame.setObjectName("workspaceFrame")
        workspace_layout = QHBoxLayout(workspace_frame)
        workspace_layout.setContentsMargins(6, 6, 6, 6)
        workspace_layout.setSpacing(6)

        # Colonne Gauche : Modèles & SoC
        self.model_selector = ModelSelectorPanel()
        self.model_selector.model_selected.connect(self._on_model_selected)
        workspace_layout.addWidget(self.model_selector)

        # Colonne Centrale : Boutons d'Action & Onglets
        self.action_tabs = ActionTabsPanel()
        self.action_tabs.action_triggered.connect(self._handle_action_triggered)
        workspace_layout.addWidget(self.action_tabs, stretch=1)

        # Colonne Droite : Liaison Matérielle & Statut
        self.conn_manager = ConnectionManagerPanel()
        self.conn_manager.rescan_requested.connect(self._on_rescan_clicked)
        workspace_layout.addWidget(self.conn_manager)

        self.vertical_splitter.addWidget(workspace_frame)

        # Console de logs détaillée en bas
        self.log_panel = LogPanel()
        self.vertical_splitter.addWidget(self.log_panel)

        # Répartition équilibrée de l'espace (540px pour les actions, 180px pour les logs)
        self.vertical_splitter.setSizes([540, 180])
        main_layout.addWidget(self.vertical_splitter, stretch=1)

    # ------------------------------------------------------------------
    # Menus et barre de statut
    # ------------------------------------------------------------------
    def _create_menu_bar(self):
        menubar = self.menuBar()

        menu_file = menubar.addMenu("&Fichier")
        act_exit = menu_file.addAction("Quitter")
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)

        menu_tools = menubar.addMenu("&Outils")
        act_rescan = menu_tools.addAction("Forcer l'analyse USB (F5)")
        act_rescan.setShortcut("F5")
        act_rescan.triggered.connect(self._on_rescan_clicked)
        menu_tools.addSeparator()
        act_adb_reset = menu_tools.addAction("📱 Factory Reset (ADB)")
        act_adb_reset.triggered.connect(lambda: self._handle_action_triggered("ADB_FACTORY_RESET", {}))
        menu_tools.addSeparator()
        act_clear = menu_tools.addAction("Effacer la console")
        act_clear.triggered.connect(self.log_panel.clear_logs)

        menu_brands = menubar.addMenu("&Marques")
        for b_id, name in [
            ("MEDIATEK", "MediaTek Universal"),
            ("INFINIX", "Infinix Mobile"),
            ("TECNO", "Tecno Mobile"),
            ("SAMSUNG", "Samsung Galaxy"),
            ("XIAOMI", "Xiaomi / Redmi / POCO"),
            ("OPPO", "Oppo / Realme"),
            ("VIVO", "Vivo Mobile")
        ]:
            act_b = menu_brands.addAction(name)
            act_b.triggered.connect(lambda ch, brand=b_id: self.brand_bar.select_brand(brand))

        menu_help = menubar.addMenu("&Aide")
        act_about = menu_help.addAction("À propos d'Optima MTK Tool Pro")
        act_about.triggered.connect(self._show_about)

    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.heartbeat_label = QLabel("● Surveillance continue USB (1.5s)")
        self.heartbeat_label.setStyleSheet(f"color: {COLOR_ACCENT_BLUE}; font-size: 10px; margin-right: 15px;")
        self.status_bar.addWidget(self.heartbeat_label)

        self.status_label = QLabel("Aucun appareil connecté")
        self.status_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        self.status_bar.addPermanentWidget(self.status_label)

    def _apply_global_stylesheet(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLOR_DARK_BG};
            }}
            QWidget#centralWidget {{
                background-color: {COLOR_DARK_BG};
            }}
            QFrame#workspaceFrame {{
                background-color: {COLOR_DARK_BG};
            }}
            QSplitter::handle:vertical {{
                background-color: {COLOR_BORDER};
                height: 4px;
            }}
            QSplitter::handle:vertical:hover {{
                background-color: {COLOR_ACCENT_BLUE};
            }}
            QStatusBar {{
                background-color: {COLOR_PANEL_BG};
                color: {COLOR_TEXT_MUTED};
                border-top: 1px solid {COLOR_BORDER};
            }}
            QMenuBar {{
                background-color: {COLOR_PANEL_BG};
                color: {COLOR_TEXT_PRIMARY};
                border-bottom: 1px solid {COLOR_BORDER};
                padding: 2px;
            }}
            QMenuBar::item:selected {{
                background-color: {COLOR_ACCENT_BLUE};
                color: #ffffff;
                border-radius: 3px;
            }}
            QMenu {{
                background-color: {COLOR_PANEL_BG};
                color: {COLOR_TEXT_PRIMARY};
                border: 1px solid {COLOR_BORDER};
            }}
            QMenu::item:selected {{
                background-color: {COLOR_ACCENT_BLUE};
                color: #ffffff;
            }}
        """)

    # ------------------------------------------------------------------
    # Navigation et événements
    # ------------------------------------------------------------------
    def _on_brand_changed(self, brand_id: str):
        self.model_selector.load_brand(brand_id)
        self._append_log(f"[+] Marque sélectionnée : {brand_id.upper()}", "info")

    def _on_model_selected(self, model_data: Dict[str, Any]):
        self.action_tabs.update_selected_model(model_data)

    def _on_rescan_clicked(self):
        self._append_log("[+] Analyse immédiate des ports USB/ADB/Fastboot déclenchée...", "info")
        dev = self.detector.scan_now(force_refresh=True)
        if dev:
            self._append_log(f"[✓] Analyse terminée : {dev.badge_title} ({dev.identifier})", "success")
        else:
            self._append_log("[i] Analyse terminée : Aucun appareil détecté.", "info")

    def _on_status_updated(self, mode_str: str, title: str, subtitle: str, color: str):
        self.status_banner.update_status(mode_str, title, subtitle, color)

    # ------------------------------------------------------------------
    # Détection USB en temps réel
    # ------------------------------------------------------------------
    def _on_device_detected(self, device: ConnectedDevice):
        self.mtk_comm.set_device(device)
        self.conn_manager.update_connection_state(device)
        loc = device.port or device.serial_number or device.identifier
        self.status_label.setText(f"{device.status_emoji} {device.badge_title} ({loc})")
        self.status_label.setStyleSheet(f"color: {device.color}; font-weight: bold;")

    def _on_device_lost(self, device: ConnectedDevice):
        self.mtk_comm.disconnect()
        self.conn_manager.update_connection_state(None)
        self.status_label.setText("🔴 Aucun appareil connecté")
        self.status_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

    # ------------------------------------------------------------------
    # Routeur d'actions avec retour en direct
    # ------------------------------------------------------------------
    def _handle_action_triggered(self, action_key: str, options: dict):
        selected_model = self.model_selector.get_selected_model()
        model_name = selected_model.get("model", "Appareil") if selected_model else "Appareil"

        self._append_log("--------------------------------------------------", "info")
        self._append_log(f"[+] Action déclenchée : {action_key} (Cible : {model_name})", "info")

        # ── 1. SECURITY / FRP ─────────────────────────────────────────
        if action_key == "BROM_ERASE_FRP":
            self.run_action_with_assistant(
                action_name="[BROM] Effacer FRP",
                operation_func=lambda dev: erase_frp(DeviceMode.BROM, dev.port or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.BROM],
                custom_instructions="1. Éteignez le téléphone.\n2. Maintenez Volume Bas.\n3. Insérez le câble USB."
            )

        elif action_key == "FASTBOOT_ERASE_FRP":
            self.run_action_with_assistant(
                action_name="[FASTBOOT] Effacer FRP",
                operation_func=lambda dev: erase_frp(DeviceMode.FASTBOOT, dev.serial_number or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.FASTBOOT],
                custom_instructions="1. Démarrez en Fastboot (Vol- & Power).\n2. Connectez le câble USB."
            )

        elif action_key == "SAMSUNG_ERASE_FRP":
            self.run_action_with_assistant(
                action_name="[SAMSUNG] Effacer FRP Knox",
                operation_func=lambda dev: erase_frp(DeviceMode.BROM, dev.port or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.BROM],
                custom_instructions="1. Éteignez le Samsung Galaxy.\n2. Maintenez Vol+ et Vol- enfoncés.\n3. Branchez le câble USB."
            )

        elif action_key == "BROM_UNLOCK_BL":
            self.run_action_with_assistant(
                action_name="[BROM] Déverrouiller Bootloader",
                operation_func=lambda dev: unlock_bootloader(DeviceMode.BROM, dev.port or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.BROM]
            )

        elif action_key == "BROM_RELOCK_BL":
            self.run_action_with_assistant(
                action_name="[BROM] Reverrouiller Bootloader",
                operation_func=lambda dev: relock_bootloader(DeviceMode.BROM, dev.port or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.BROM]
            )

        elif action_key == "FASTBOOT_OEM_UNLOCK":
            self.run_action_with_assistant(
                action_name="[FASTBOOT] OEM Unlock",
                operation_func=lambda dev: unlock_bootloader(DeviceMode.FASTBOOT, dev.serial_number or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.FASTBOOT]
            )

        # ── 2. FUNCTION ───────────────────────────────────────────────
        elif action_key == "BROM_FACTORY_RESET":
            reply = QMessageBox.warning(
                self, "Confirmation Factory Reset",
                f"<b>ATTENTION : TOUTES LES DONNÉES DE L'APPAREIL SERONT EFFACÉES.</b><br><br>"
                f"Cible : {model_name}<br>"
                f"Voulez-vous procéder au formatage complet de la partition userdata ?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.run_action_with_assistant(
                    action_name="[BROM] Factory Reset",
                    operation_func=lambda dev: factory_reset(DeviceMode.BROM, dev.port or dev.identifier, log_callback=self._append_log),
                    target_modes=[DeviceMode.BROM]
                )

        elif action_key == "ADB_FACTORY_RESET":
            reply = QMessageBox.warning(
                self,
                "Confirmation Factory Reset (ADB)",
                "<b>ATTENTION : CETTE ACTION EFFACERA TOUTES LES DONNÉES DE L'APPAREIL !</b><br><br>"
                f"Cible : {model_name}<br><br>"
                "Cette commande va réinitialiser le smartphone aux paramètres d'usine via le pont ADB.<br>"
                "• Photos, musiques, fichiers personnels et applications seront supprimés.<br>"
                "• Les comptes et verrouillages écran seront effacés.<br><br>"
                "Êtes-vous certain de vouloir continuer ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.run_action_with_assistant(
                    action_name="[ADB] Factory Reset",
                    operation_func=self._execute_adb_factory_reset_action,
                    target_modes=[DeviceMode.ADB, DeviceMode.NORMAL],
                    custom_instructions="1. Allumez le téléphone normalement dans Android.\n2. Activez le Débogage USB dans les Options de développement.\n3. Branchez le câble USB et autorisez le débogage sur l'écran."
                )

        elif action_key == "BROM_SAFE_FORMAT":
            self.run_action_with_assistant(
                action_name="[BROM] Safe Format",
                operation_func=lambda dev: factory_reset(DeviceMode.BROM, dev.port or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.BROM]
            )

        elif action_key == "BROM_READ_INFO":
            self.run_action_with_assistant(
                action_name="[BROM] Lire Infos Matérielles",
                operation_func=lambda dev: read_device_info(DeviceMode.BROM, dev.port or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.BROM]
            )

        elif action_key == "BROM_REMOVE_DEMO":
            self.run_action_with_assistant(
                action_name="[BROM] Supprimer Démo / PayJoy",
                operation_func=lambda dev: erase_frp(DeviceMode.BROM, dev.port or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.BROM]
            )

        elif action_key == "ADB_READ_INFO":
            self.run_action_with_assistant(
                action_name="[ADB] Lire Spécifications Système",
                operation_func=lambda dev: read_device_info(DeviceMode.ADB, dev.serial_number or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.ADB, DeviceMode.NORMAL]
            )

        elif action_key == "BROM_AUTH_BYPASS":
            self.run_action_with_assistant(
                action_name="[BROM] Bypass SLA / DAA",
                operation_func=lambda dev: read_device_info(DeviceMode.BROM, dev.port or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.BROM]
            )

        # ── 3. FASTBOOT ───────────────────────────────────────────────
        elif action_key == "FASTBOOT_GETVAR":
            self.run_action_with_assistant(
                action_name="[FASTBOOT] Getvar All",
                operation_func=lambda dev: read_device_info(DeviceMode.FASTBOOT, dev.serial_number or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.FASTBOOT]
            )

        elif action_key == "FASTBOOT_ERASE_USERDATA":
            self.run_action_with_assistant(
                action_name="[FASTBOOT] Erase Userdata",
                operation_func=lambda dev: factory_reset(DeviceMode.FASTBOOT, dev.serial_number or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.FASTBOOT]
            )

        elif action_key == "REBOOT_NORMAL":
            self._execute_reboot_direct("normal")

        elif action_key == "REBOOT_FASTBOOT":
            self._execute_reboot_direct("fastboot")

        elif action_key == "REBOOT_RECOVERY":
            self._execute_reboot_direct("recovery")

        elif action_key == "FASTBOOT_OEM_CLEAR":
            self.run_action_with_assistant(
                action_name="[FASTBOOT] OEM Clear",
                operation_func=lambda dev: erase_frp(DeviceMode.FASTBOOT, dev.serial_number or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.FASTBOOT]
            )

        # ── 4. RECOVERY ───────────────────────────────────────────────
        elif action_key == "RECOVERY_READ_INFO":
            self.run_action_with_assistant(
                action_name="[RECOVERY] Lire Infos",
                operation_func=lambda dev: read_device_info(DeviceMode.ADB, dev.serial_number or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.ADB, DeviceMode.NORMAL]
            )

        elif action_key == "RECOVERY_FORMAT":
            self.run_action_with_assistant(
                action_name="[RECOVERY] Format Data",
                operation_func=lambda dev: factory_reset(DeviceMode.FASTBOOT, dev.serial_number or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.FASTBOOT, DeviceMode.BROM]
            )

        # ── 5. META ───────────────────────────────────────────────────
        elif action_key in ("META_READ_INFO", "META_FACTORY_RESET", "META_BACKUP_NV", "META_REBOOT_NORMAL"):
            self.run_action_with_assistant(
                action_name=f"[META] {action_key}",
                operation_func=lambda dev: read_device_info(DeviceMode.BROM, dev.port or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.BROM]
            )

    def _execute_reboot_direct(self, target: str):
        if target == "fastboot":
            current = self.detector.get_current_device()
            # Sécurité d'exécution : vérifier d'abord si un appareil est bien connecté en mode ADB
            if not current or current.mode != DeviceMode.ADB:
                self._append_log("Erreur : Aucun appareil en mode ADB actif", "warning")
                return

            from core.actions import reboot_to_fastboot
            serial = current.serial_number or current.identifier
            reboot_to_fastboot(device_serial=serial, log_callback=self._append_log)
            return

        current = self.detector.get_current_device()
        if current:
            target_id = current.port or current.serial_number or current.identifier
            reboot_device(current.mode, target_id, target_reboot=target, log_callback=self._append_log)
        else:
            self._append_log(f"[WARNING] Aucun appareil connecté pour redémarrage vers {target}.", "warning")

    def _execute_adb_factory_reset_action(self, dev: Optional[ConnectedDevice] = None):
        """Exécute la réinitialisation d'usine via ADB avec journalisation et boîte de dialogue de retour."""
        device_id = None
        if dev:
            device_id = dev.serial_number or dev.identifier
        self._append_log("[+] Lancement du Factory Reset via le pont ADB...", "info")
        res = factory_reset_adb(device_identifier=device_id, log_callback=self._append_log)
        if res.success:
            self._append_log(f"[SUCCESS] {res.message}", "success")
            QMessageBox.information(
                self,
                "Factory Reset (ADB) Réussi",
                f"<b>Succès :</b> {res.message}<br><br>L'appareil a reçu l'instruction et redémarre avec les paramètres d'usine d'origine."
            )
        else:
            self._append_log(f"[ERROR] {res.message}", "error")
            QMessageBox.critical(
                self,
                "Échec du Factory Reset (ADB)",
                f"L'opération a échoué :<br><br><b>{res.message}</b>"
            )

    def run_action_with_assistant(
        self,
        action_name: str,
        operation_func: Callable[[ConnectedDevice], None],
        target_modes: Optional[List[DeviceMode]] = None,
        custom_instructions: Optional[str] = None,
        timeout: int = 60
    ) -> bool:
        current = self.detector.get_current_device()
        if current is not None:
            mode_ok = (target_modes is None) or (current.mode in target_modes)
            if mode_ok:
                loc = current.port or current.serial_number or current.identifier
                self._append_log(
                    f"Appareil déjà connecté ({current.mode.value} — {loc}). "
                    f"Exécution immédiate de « {action_name} »...",
                    "success"
                )
                self._on_device_detected(current)
                operation_func(current)
                return True

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
        self.log_panel.add_log(message, level)

    def _show_about(self):
        QMessageBox.about(
            self,
            "À propos d'Optima MTK Tool Pro",
            "<b>Optima MTK Tool Pro</b> v2.0<br><br>"
            "Suite logicielle professionnelle d'atelier pour le diagnostic, le flash et "
            "le déblocage FRP des processeurs <b>MediaTek</b>.<br><br>"
            "• Ergonomie TFT Unlock Tool (Multi-marques)<br>"
            "• Gestionnaire USB & Matériel en direct<br>"
            "• Support Infinix, Tecno, Samsung, Xiaomi, Oppo, Vivo, MTK<br><br>"
            "© Optima Telecom — Tous droits réservés"
        )

    def closeEvent(self, event):
        if self.mtk_comm.is_connected():
            reply = QMessageBox.question(
                self, "Quitter l'application",
                "Un appareil est encore synchronisé. Voulez-vous vraiment quitter ?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return

        self.detector.stop_monitoring()
        event.accept()
