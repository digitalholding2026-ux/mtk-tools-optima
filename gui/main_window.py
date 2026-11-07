# -*- coding: utf-8 -*-
"""
Fenêtre principale d'Optima MTK Tool Pro.
Interface épurée : en-tête (marque + statut appareil), panneau d'actions central,
console de logs essentielle, infobulles et guide contextuel.
"""

import os
import sys
from typing import Optional, Dict, Any, List

_gui_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_gui_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStatusBar, QMessageBox, QFrame, QSplitter, QLabel
)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont

from .tft_widgets import (
    BrandTabBar, ModelSelectorPanel, ActionTabsPanel, ConnectionManagerPanel,
    COLOR_DARK_BG, COLOR_PANEL_BG, COLOR_BORDER, COLOR_ACCENT_BLUE,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_MUTED, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER
)
from .log_panel import LogPanel
from .device_status_widget import DeviceStatusBanner
from core.detector import DeviceDetector, ConnectedDevice, DeviceMode
from core.mtk_communication import MTKCommunication
from core.actions import (
    erase_frp, factory_reset, factory_reset_adb, read_device_info, read_device_info_adb,
    reboot_device,
    unlock_bootloader, relock_bootloader,
    samsung_frp_testmode, samsung_read_info_mtp, bypass_mi_account,
    remove_mdm_payjoy, bypass_oppo_id, ActionResult
)

from core.license_manager import LicenseManager
from .license_widget import LicenseWidget


# Instructions d'atelier dynamiques par action (badge -> guide court)
WORKSHOP_GUIDES: Dict[str, str] = {
    "BROM_ERASE_FRP": "1. Éteignez le téléphone.\n2. Maintenez Volume Bas.\n3. Branchez le câble USB.\nLe compte Google (FRP) sera supprimé en mode BROM.",
    "FASTBOOT_ERASE_FRP": "1. Démarrez en Fastboot (Vol- + Power).\n2. Connectez le câble USB.\nLe compte Google (FRP) sera supprimé en mode Fastboot.",
    "SAMSUNG_ERASE_FRP": "1. Éteignez le Samsung Galaxy.\n2. Maintenez Vol+ et Vol-.\n3. Branchez le câble USB.\nLe FRP et Knox seront supprimés en mode BROM.",
    "SAMSUNG_FRP_TESTMODE": "1. Allumez le Galaxy sur l'écran d'urgence.\n2. Composez *#0*# pour ouvrir le menu de test.\n3. Branchez le câble USB en mode MTP/ADB.",
    "SAMSUNG_READ_INFO_MTP": "Branchez le Samsung allumé en mode MTP (Transfert de fichiers) pour lire les informations.",
    "SAMSUNG_KNOX_ENROLL": "Branchez le Samsung allumé pour neutraliser les services Knox Enrollment et MDM.",
    "SAMSUNG_REBOOT_DOWNLOAD": "L'adb bascule le Samsung en mode Download (Odin) pour le flash PC.",
    "XIAOMI_MI_ACCOUNT_BYPASS": "1. Éteignez le Xiaomi.\n2. Maintenez Vol- (ou TestPoint BROM).\n3. Branchez le câble USB.\nLe compte Mi/HeyTap sera contourné.",
    "TRANSSION_REMOVE_MDM": "1. Éteignez l'appareil Infinix/Tecno.\n2. Maintenez Vol-.\n3. Branchez le câble USB.\nLes profils MDM / PayJoy seront supprimés.",
    "OPPO_ID_BYPASS": "1. Éteignez l'appareil Oppo/Realme.\n2. Maintenez Vol+ et Vol-.\n3. Branchez le câble USB.\nLe compte Oppo/HeyTap sera contourné.",
    "BROM_UNLOCK_BL": "Déverrouille le bootloader MediaTek en mode BROM pour installer des recoveries custom.",
    "BROM_RELOCK_BL": "Reverrouille le bootloader MediaTek en mode BROM pour restaurer la sécurité d'usine.",
    "FASTBOOT_OEM_UNLOCK": "Exécute 'fastboot oem unlock' pour déverrouiller le bootloader Android en mode Fastboot.",
    "READ_INFO_ADB": "Lit les spécifications de l'appareil Android via le pont ADB (Débogage USB requis).",
    "BROM_FACTORY_RESET": "ATTENTION : efface toutes les données utilisateur (partition userdata) en mode BROM. Irréversible.",
    "ADB_FACTORY_RESET": "Réinitialise l'appareil Android aux paramètres d'usine via ADB. Toutes les données seront supprimées.",
    "BROM_SAFE_FORMAT": "Formatage sécurisé des partitions utilisateur en mode BROM (sans toucher aux partitions boot/recovery).",
    "BROM_READ_INFO": "Lit les informations matérielles (chipset, version, mémoire) en mode Preloader/BROM.",
    "BROM_REMOVE_DEMO": "Supprime le mode Démo et PayJoy sur les appareils MediaTek en mode BROM.",
    "ADB_READ_INFO": "Lit les spécifications système complètes (Android, modèle, constructeur) via ADB.",
    "BROM_AUTH_BYPASS": "Bypasse l'authentification SLA/DAA sur les processeurs MediaTek en mode BROM pour autoriser le flash.",
    "FASTBOOT_GETVAR": "Affiche toutes les variables Fastboot (version, serial, statut déverrouillage) de l'appareil.",
    "FASTBOOT_ERASE_USERDATA": "Formate la partition userdata de l'appareil Android en mode Fastboot. Données supprimées.",
    "REBOOT_NORMAL": "Redémarre l'appareil connecté vers le mode normal (Android).",
    "REBOOT_FASTBOOT": "Redémarre l'appareil Android (en mode ADB) vers le mode Fastboot.",
    "REBOOT_RECOVERY": "Redémarre l'appareil connecté vers le mode Recovery pour maintenance et flash.",
    "FASTBOOT_OEM_CLEAR": "Exécute 'fastboot oem clear' pour effacer les données et verrous OEM en mode Fastboot.",
    "RECOVERY_READ_INFO": "Lit les informations de l'appareil Android en mode Recovery ou ADB.",
    "RECOVERY_FORMAT": "Formate la partition Data en mode Recovery ou Fastboot. Toutes les données utilisateur sont supprimées.",
    "META_READ_INFO": "Lit les informations de l'appareil en mode META (MediaTek).",
    "META_FACTORY_RESET": "Réinitialise l'appareil en mode META (MediaTek).",
    "META_BACKUP_NV": "Sauvegarde la partition NV en mode META (MediaTek).",
    "META_REBOOT_NORMAL": "Redémarre l'appareil en mode META vers le mode normal.",
}


class MainWindow(QMainWindow):
    """Fenêtre principale d'Optima MTK Tool Pro — interface épurée avec aide contextuelle."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Optima MTK Tool Pro")
        self.setMinimumSize(1100, 720)
        self.resize(1240, 820)

        self.mtk_comm = MTKCommunication()
        self.detector = DeviceDetector(interval=1.5)
        self.com_detector = self.detector

        self._setup_ui()
        self._apply_global_stylesheet()
        self._create_menu_bar()
        self._create_status_bar()

        self.license_mgr = LicenseManager()
        self._license_blocked = False
        self._setup_license_ui()
        self._check_license_startup()

        self.detector.device_detected.connect(self._on_device_detected)
        self.detector.device_lost.connect(self._on_device_lost)
        self.detector.status_updated.connect(self._on_status_updated)
        self.detector.log_message.connect(self._append_log)

        self.log_panel.add_log("Optima MTK Tool Pro initialisé.", "success")
        self.detector.start_monitoring()

    def _setup_ui(self):
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. En-tête : marque + statut appareil
        self.brand_bar = BrandTabBar()
        self.brand_bar.brand_changed.connect(self._on_brand_changed)
        main_layout.addWidget(self.brand_bar)

        self.license_widget = LicenseWidget()
        self.license_widget.set_activate_callback(self._on_license_activate_requested)
        main_layout.addWidget(self.license_widget)

        self.status_banner = DeviceStatusBanner()
        main_layout.addWidget(self.status_banner)

        # 2. QSplitter Vertical (Espace de travail + Console)
        self.vertical_splitter = QSplitter(Qt.Vertical)
        self.vertical_splitter.setObjectName("verticalSplitter")
        self.vertical_splitter.setHandleWidth(4)

        workspace_frame = QFrame()
        workspace_frame.setObjectName("workspaceFrame")
        workspace_layout = QHBoxLayout(workspace_frame)
        workspace_layout.setContentsMargins(6, 6, 6, 6)
        workspace_layout.setSpacing(6)

        self.model_selector = ModelSelectorPanel()
        self.model_selector.model_selected.connect(self._on_model_selected)
        workspace_layout.addWidget(self.model_selector)

        self.action_tabs = ActionTabsPanel()
        self.action_tabs.action_triggered.connect(self._handle_action_triggered)
        self.action_tabs.action_hovered.connect(self._on_action_hovered)
        workspace_layout.addWidget(self.action_tabs, stretch=1)

        self.conn_manager = ConnectionManagerPanel()
        self.conn_manager.rescan_requested.connect(self._on_rescan_clicked)
        workspace_layout.addWidget(self.conn_manager)

        self.vertical_splitter.addWidget(workspace_frame)

        self.log_panel = LogPanel()
        self.vertical_splitter.addWidget(self.log_panel)

        self.vertical_splitter.setSizes([640, 160])
        main_layout.addWidget(self.vertical_splitter, stretch=1)

    def _create_menu_bar(self):
        menubar = self.menuBar()

        menu_file = menubar.addMenu("&Fichier")
        act_exit = menu_file.addAction("Quitter")
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)

        menu_tools = menubar.addMenu("&Outils")
        act_rescan = menu_tools.addAction("Analyser USB (F5)")
        act_rescan.setShortcut("F5")
        act_rescan.triggered.connect(self._on_rescan_clicked)
        menu_tools.addSeparator()
        act_clear = menu_tools.addAction("Effacer la console")
        act_clear.triggered.connect(self.log_panel.clear_logs)

        menu_help = menubar.addMenu("&Aide")
        act_about = menu_help.addAction("À propos")
        act_about.triggered.connect(self._show_about)

    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Aucun appareil connecté")
        self.status_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        self.status_bar.addPermanentWidget(self.status_label)

    def _setup_license_ui(self):
        self.license_widget.license_activated.connect(self._on_license_activated)

    def _check_license_startup(self):
        is_valid, msg, _ = self.license_mgr.is_license_valid()
        self._license_blocked = not is_valid
        if not is_valid:
            self._append_log(f"Licence : {msg}", "warning")

    def _on_license_activate_requested(self):
        from gui.license_dialog import LicenseDialog
        dlg = LicenseDialog(self)
        if dlg.exec_() == dlg.Accepted:
            self._on_license_activated()

    def _on_license_activated(self):
        self._check_license_startup()
        self.license_widget._refresh()

    def _is_action_allowed(self) -> bool:
        is_valid, msg, _ = self.license_mgr.is_license_valid()
        self._license_blocked = not is_valid
        if not is_valid:
            self._append_log(f"Licence : {msg}", "warning")
        return is_valid

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

    def _on_brand_changed(self, brand_id: str):
        self.model_selector.load_brand(brand_id)
        self.update_dynamic_menu(brand_id)
        self._append_log(f"Marque : {brand_id.upper()}", "info")

    def _on_model_selected(self, model_data: Dict[str, Any]):
        brand_id = model_data.get("brand_id", self.brand_bar.get_active_brand())
        self.update_dynamic_menu(brand_id, model_data)
        self._append_log(f"Modèle : {model_data.get('model', 'Inconnu')} ({model_data.get('chipset', 'MTK')})", "info")

    def update_dynamic_menu(self, brand_name: str, model_data: Optional[Dict[str, Any]] = None):
        b_id = (brand_name or "MEDIATEK").upper()
        self.action_tabs.load_brand_actions(b_id, model_data)
        self.conn_manager.update_workshop_instructions(b_id)
        if hasattr(self, "brand_bar") and self.brand_bar.get_active_brand().upper() != b_id:
            self.brand_bar.select_brand(b_id, notify=False)

    def _on_rescan_clicked(self):
        self._append_log("Analyse des ports USB/ADB/Fastboot...", "info")
        dev = self.detector.scan_now(force_refresh=True)
        if dev:
            self._append_log(f"Appareil détecté : {dev.badge_title}", "success")
        else:
            self._append_log("Aucun appareil détecté.", "info")

    @pyqtSlot(str, str, str, str)
    def _on_status_updated(self, mode_str: str, title: str, subtitle: str, color: str):
        self.status_banner.update_status(mode_str, title, subtitle, color)

    def _on_action_hovered(self, action_key: str):
        """Affiche le guide d'atelier contextuel quand la souris survole un bouton d'action."""
        guide = WORKSHOP_GUIDES.get(action_key, "")
        if guide:
            self.conn_manager.show_contextual_guide(action_key, guide)

    def _on_device_detected(self, device: ConnectedDevice):
        self.mtk_comm.set_device(device)
        self.conn_manager.update_connection_state(device)
        loc = device.port or device.serial_number or device.identifier
        self.status_label.setText(f"{device.status_emoji} {device.badge_title} ({loc})")
        self.status_label.setStyleSheet(f"color: {device.color}; font-weight: bold;")

    def _on_device_lost(self, device: ConnectedDevice):
        self.mtk_comm.disconnect()
        self.conn_manager.update_connection_state(None)
        self.status_label.setText("Aucun appareil connecté")
        self.status_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED};")

    def _handle_action_triggered(self, action_key: str, options: dict):
        if not self._is_action_allowed():
            return

        selected_model = self.model_selector.get_selected_model()
        model_name = selected_model.get("model", "Appareil") if selected_model else "Appareil"

        self._append_log(f"Action : {action_key} (Cible : {model_name})", "info")

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
        elif action_key == "SAMSUNG_FRP_TESTMODE":
            self.run_action_with_assistant(
                action_name="[SAMSUNG] FRP (*#0*#)",
                operation_func=lambda dev: samsung_frp_testmode(log_callback=self._append_log),
                target_modes=[DeviceMode.ADB, DeviceMode.USB_NORMAL, DeviceMode.NORMAL],
                custom_instructions="1. Allumez le Galaxy.\n2. Écran d'urgence.\n3. Composez *#0*#.\n4. Branchez le câble USB."
            )
        elif action_key == "SAMSUNG_READ_INFO_MTP":
            self.run_action_with_assistant(
                action_name="[SAMSUNG] Lecture Infos MTP",
                operation_func=lambda dev: samsung_read_info_mtp(log_callback=self._append_log),
                target_modes=[DeviceMode.ADB, DeviceMode.USB_NORMAL, DeviceMode.NORMAL],
                custom_instructions="Branchez le Samsung allumé en mode MTP (Transfert de fichiers)."
            )
        elif action_key == "SAMSUNG_KNOX_ENROLL":
            self.run_action_with_assistant(
                action_name="[SAMSUNG] Désactiver Knox Enrollment",
                operation_func=lambda dev: remove_mdm_payjoy(dev.mode, dev.port or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.ADB, DeviceMode.BROM],
                custom_instructions="Branchez le Samsung pour neutraliser les services Knox Enrollment."
            )
        elif action_key == "SAMSUNG_REBOOT_DOWNLOAD":
            self._execute_reboot_direct("download")
        elif action_key == "XIAOMI_MI_ACCOUNT_BYPASS":
            self.run_action_with_assistant(
                action_name="[XIAOMI] Bypass Mi Account",
                operation_func=lambda dev: bypass_mi_account(dev.mode, dev.port or dev.serial_number or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.BROM, DeviceMode.FASTBOOT],
                custom_instructions="1. Éteignez le Xiaomi.\n2. Maintenez Vol- (ou TestPoint BROM).\n3. Insérez le câble USB."
            )
        elif action_key == "TRANSSION_REMOVE_MDM":
            self.run_action_with_assistant(
                action_name="[TRANSSION] Suppression MDM / PayJoy",
                operation_func=lambda dev: remove_mdm_payjoy(dev.mode, dev.port or dev.serial_number or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.BROM],
                custom_instructions="1. Éteignez l'appareil (Infinix/Tecno).\n2. Maintenez Vol-.\n3. Insérez le câble USB."
            )
        elif action_key == "OPPO_ID_BYPASS":
            self.run_action_with_assistant(
                action_name="[OPPO/REALME] Bypass Oppo ID / HeyTap",
                operation_func=lambda dev: bypass_oppo_id(dev.mode, dev.port or dev.serial_number or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.BROM],
                custom_instructions="1. Éteignez l'appareil Oppo/Realme.\n2. Maintenez Vol+ et Vol-.\n3. Insérez le câble USB."
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
        elif action_key == "READ_INFO_ADB":
            dev = self.detector.get_current_device()
            if not dev or dev.mode != DeviceMode.ADB:
                self._append_log("Aucun appareil en mode ADB actif.", "error")
                QMessageBox.warning(
                    self, "Lecture Infos ADB",
                    "Aucun appareil connecté en mode ADB (Débogage USB).\n"
                    "Activez le Débogage USB et branchez le câble."
                )
                return
            self.run_action_with_assistant(
                action_name="[ADB] Lecture Infos Appareil",
                operation_func=lambda d: read_device_info_adb(
                    device_identifier=d.serial_number or d.identifier,
                    log_callback=self._append_log
                ),
                target_modes=[DeviceMode.ADB],
                custom_instructions="L'appareil doit être connecté en mode ADB (Débogage USB activé)."
            )
        elif action_key == "BROM_FACTORY_RESET":
            reply = QMessageBox.warning(
                self, "Confirmation Factory Reset",
                f"<b>ATTENTION : TOUTES LES DONNÉES SERONT EFFACÉES.</b><br><br>"
                f"Cible : {model_name}<br>"
                f"Procéder au formatage complet de la partition userdata ?",
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
                "Cette commande va réinitialiser le smartphone aux paramètres d'usine via ADB.<br>"
                "Êtes-vous certain de vouloir continuer ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.run_action_with_assistant(
                    action_name="[ADB] Factory Reset",
                    operation_func=self._execute_adb_factory_reset_action,
                    target_modes=[DeviceMode.ADB, DeviceMode.NORMAL],
                    custom_instructions="1. Allumez le téléphone normalement.\n2. Activez le Débogage USB.\n3. Branchez le câble USB et autorisez le débogage."
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
        elif action_key in ("META_READ_INFO", "META_FACTORY_RESET", "META_BACKUP_NV", "META_REBOOT_NORMAL"):
            self.run_action_with_assistant(
                action_name=f"[META] {action_key}",
                operation_func=lambda dev: read_device_info(DeviceMode.BROM, dev.port or dev.identifier, log_callback=self._append_log),
                target_modes=[DeviceMode.BROM]
            )

    def _execute_reboot_direct(self, target: str):
        if target == "download":
            from core.actions import find_adb
            adb_bin = find_adb() or "adb"
            self._append_log("Envoi de la commande 'adb reboot download'...", "info")
            try:
                subprocess_run = __import__('subprocess').run([adb_bin, "reboot", "download"], capture_output=True, timeout=5)
                self._append_log("Commande 'adb reboot download' envoyée.", "success")
            except Exception as e:
                self._append_log(f"Échec reboot download : {e}", "error")
            return

        if target == "fastboot":
            current = self.detector.get_current_device()
            if not current or current.mode != DeviceMode.ADB:
                self._append_log("Aucun appareil en mode ADB actif", "warning")
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
            self._append_log(f"Aucun appareil connecté pour redémarrage vers {target}.", "warning")

    def _execute_adb_factory_reset_action(self, dev: Optional[ConnectedDevice] = None):
        device_id = None
        if dev:
            device_id = dev.serial_number or dev.identifier
        self._append_log("Lancement du Factory Reset via ADB...", "info")
        res = factory_reset_adb(device_identifier=device_id, log_callback=self._append_log)
        if res.success:
            self._append_log(f"Factory Reset réussi : {res.message}", "success")
            QMessageBox.information(
                self,
                "Factory Reset (ADB) Réussi",
                f"<b>Succès :</b> {res.message}<br><br>L'appareil redémarre avec les paramètres d'usine d'origine."
            )
        else:
            self._append_log(f"Échec Factory Reset (ADB) : {res.message}", "error")
            QMessageBox.critical(
                self,
                "Échec du Factory Reset (ADB)",
                f"L'opération a échoué :<br><br><b>{res.message}</b>"
            )

    def run_action_with_assistant(
        self,
        action_name: str,
        operation_func,
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
                    f"Exécution de « {action_name} »...",
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
