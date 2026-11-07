# -*- coding: utf-8 -*-
"""
Composants d'interface utilisateur professionnels type TFT Unlock Tool Pro.
Layouts 100% dynamiques, sans conteneurs bloquants, avec hauteurs adaptatives :
  1. BrandTabBar : Barre supérieure compacte de sélection des marques (44px)
  2. ModelSelectorPanel : Panneau gauche avec recherche et liste adaptative
  3. ActionTabsPanel : Panneau central avec boutons d'action d'une hauteur min de 44px,
     haut contraste, zéro texte masqué ou tronqué
  4. ConnectionManagerPanel : Panneau droit compact avec statut matériel temps réel
"""

from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem, QTabWidget,
    QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont

from core.device_models import SUPPORTED_BRANDS, DEVICES_DATABASE, get_models_for_brand, search_models
from core.detector import ConnectedDevice, DeviceMode

# Palette de couleurs TFT Unlock Pro (Haut contraste / Dark Mode)
COLOR_DARK_BG       = "#090c13"
COLOR_PANEL_BG      = "#0f1422"
COLOR_CARD_BG       = "#151b2c"
COLOR_CARD_HOVER    = "#1d253c"
COLOR_BORDER        = "#232d44"
COLOR_TEXT_PRIMARY  = "#ffffff"
COLOR_TEXT_BRIGHT   = "#f1f5f9"
COLOR_TEXT_MUTED    = "#94a3b8"
COLOR_ACCENT_BLUE   = "#00a2ff"
COLOR_CYAN          = "#00d2ff"
COLOR_SUCCESS       = "#10b981"  # Vert émeraude
COLOR_WARNING       = "#f59e0b"  # Ambre
COLOR_DANGER        = "#ef4444"  # Rouge rubis
COLOR_PURPLE        = "#a855f7"  # Violet

# Infobulles détaillées par action (badge -> titre, sous-titre, explanation)
ACTION_TOOLTIPS: Dict[str, Dict[str, str]] = {
    "BROM_ERASE_FRP": {
        "title": "[BROM] Effacer FRP",
        "subtitle": "Supprime le compte Google (FRP) en mode Preloader/BROM.",
        "explanation": "Supprime le verrou Google (FRP) sur les processeurs MediaTek en mode Preloader/BROM. Nécessite d'éteindre le téléphone, de maintenir Volume Bas, puis de brancher le câble USB.",
    },
    "FASTBOOT_ERASE_FRP": {
        "title": "[FASTBOOT] Effacer FRP",
        "subtitle": "Supprime le compte Google (FRP) en mode Fastboot.",
        "explanation": "Supprime le verrou Google (FRP) via le protocole Fastboot. L'appareil doit être démarré en mode Fastboot (Vol- + Power) et connecté par USB.",
    },
    "SAMSUNG_ERASE_FRP": {
        "title": "[SAMSUNG] Effacer FRP Knox",
        "subtitle": "Supprime le FRP sur Samsung Galaxy en mode BROM.",
        "explanation": "Supprime le verrou Google (FRP) et Knox sur les Samsung Galaxy via le mode BROM. Nécessite d'éteindre le téléphone, de maintenir Vol+ et Vol-, puis de brancher le câble USB.",
    },
    "SAMSUNG_FRP_TESTMODE": {
        "title": "[SAMSUNG] FRP (*#0*#)",
        "subtitle": "Bypass FRP via le menu de test Samsung.",
        "explanation": "Contourne le FRP sur Samsung Galaxy via le code secret *#0*# (menu de test). Le téléphone doit être allumé sur l'écran d'urgence et connecté en mode MTP/ADB.",
    },
    "SAMSUNG_READ_INFO_MTP": {
        "title": "[SAMSUNG] Lecture Infos MTP",
        "subtitle": "Lit les informations appareil via MTP.",
        "explanation": "Lit les spécifications du Samsung Galaxy connecté en mode MTP (Transfert de fichiers). Le téléphone doit être allumé et en mode transfert de fichiers.",
    },
    "SAMSUNG_KNOX_ENROLL": {
        "title": "[SAMSUNG] Désactiver Knox Enrollment",
        "subtitle": "Neutralise les services Knox Enrollment/MDM.",
        "explanation": "Désactive l'inscription Knox Enrollment et les profils MDM sur les appareils Samsung. Connectez l'appareil allumé en mode ADB ou BROM.",
    },
    "SAMSUNG_REBOOT_DOWNLOAD": {
        "title": "[SAMSUNG] Redémarrer en Download",
        "subtitle": "Bascule le Samsung en mode Download (Odin).",
        "explanation": "Envoie la commande 'adb reboot download' pour basculer le Samsung Galaxy en mode Download (Odin) permettant le flash via Odin sur PC.",
    },
    "XIAOMI_MI_ACCOUNT_BYPASS": {
        "title": "[XIAOMI] Bypass Mi Account",
        "subtitle": "Contourne le compte Mi/Xiaomi Cloud.",
        "explanation": "Supprime le verrou compte Mi/Xiaomi Cloud sur les appareils Xiaomi/Redmi/POCO en mode BROM ou Fastboot. Nécessite d'éteindre le téléphone, de maintenir Vol-, puis de brancher le câble USB.",
    },
    "TRANSSION_REMOVE_MDM": {
        "title": "[TRANSSION] Suppression MDM / PayJoy",
        "subtitle": "Supprime MDM / PayJoy sur Infinix/Tecno.",
        "explanation": "Supprime les profils MDM et PayJoy sur les appareils Transsion (Infinix, Tecno, itel) en mode BROM. Nécessite d'éteindre le téléphone, de maintenir Vol-, puis de brancher le câble USB.",
    },
    "OPPO_ID_BYPASS": {
        "title": "[OPPO/REALME] Bypass Oppo ID / HeyTap",
        "subtitle": "Contourne le compte Oppo/Realme/HeyTap.",
        "explanation": "Supprime le verrou compte Oppo ID, Realme ID ou HeyTap sur les appareils Oppo/Realme en mode BROM. Nécessite d'éteindre le téléphone, de maintenir Vol+ et Vol-, puis de brancher le câble USB.",
    },
    "BROM_UNLOCK_BL": {
        "title": "[BROM] Déverrouiller Bootloader",
        "subtitle": "Déverrouille le bootloader en mode BROM.",
        "explanation": "Déverrouille le bootloader des processeurs MediaTek en mode Preloader/BROM. Permet d'installer des recoveries custom ou des ROM modifiées.",
    },
    "BROM_RELOCK_BL": {
        "title": "[BROM] Reverrouiller Bootloader",
        "subtitle": "Reverrouille le bootloader en mode BROM.",
        "explanation": "Reverrouille le bootloader des processeurs MediaTek en mode Preloader/BROM pour restaurer la sécurité d'usine de l'appareil.",
    },
    "FASTBOOT_OEM_UNLOCK": {
        "title": "[FASTBOOT] OEM Unlock",
        "subtitle": "Déverrouille le bootloader en mode Fastboot.",
        "explanation": "Exécute 'fastboot oem unlock' pour déverrouiller le bootloader des appareils Android en mode Fastboot.",
    },
    "READ_INFO_ADB": {
        "title": "[ADB] Lecture Infos Appareil",
        "subtitle": "Lit les informations via le pont ADB.",
        "explanation": "Lit les spécifications de l'appareil Android connecté en mode ADB (Débogage USB activé).",
    },
    "BROM_FACTORY_RESET": {
        "title": "[BROM] Factory Reset",
        "subtitle": "Réinitialisation complète en mode BROM.",
        "explanation": "Efface toutes les données de l'utilisateur (partition userdata) sur les processeurs MediaTek en mode BROM. Irréversible — sauvegardez vos données avant.",
    },
    "ADB_FACTORY_RESET": {
        "title": "[ADB] Factory Reset",
        "subtitle": "Réinitialisation complète via ADB.",
        "explanation": "Réinitialise l'appareil Android aux paramètres d'usine via le pont ADB. Toutes les données personnelles, comptes et applications seront supprimées.",
    },
    "BROM_SAFE_FORMAT": {
        "title": "[BROM] Safe Format",
        "subtitle": "Formatage sécurisé en mode BROM.",
        "explanation": "Effectue un formatage sécurisé des partitions utilisateur en mode BROM sur les processeurs MediaTek, sans toucher aux partitions de boot ou de recovery.",
    },
    "BROM_READ_INFO": {
        "title": "[BROM] Lire Infos Matérielles",
        "subtitle": "Lit les spécifications matérielles en mode BROM.",
        "explanation": "Lit les informations matérielles (chipset, version, mémoire, etc.) des processeurs MediaTek en mode Preloader/BROM.",
    },
    "BROM_REMOVE_DEMO": {
        "title": "[BROM] Supprimer Démo / PayJoy",
        "subtitle": "Supprime le mode Démo et PayJoy en mode BROM.",
        "explanation": "Supprime le compte Démo / Mode Démo et PayJoy sur les appareils MediaTek en mode Preloader/BROM.",
    },
    "ADB_READ_INFO": {
        "title": "[ADB] Lire Spécifications Système",
        "subtitle": "Lit les spécifications système via ADB.",
        "explanation": "Lit les spécifications système complètes (Android, modèle, constructeur, etc.) via le pont ADB sur un appareil allumé en mode normal.",
    },
    "BROM_AUTH_BYPASS": {
        "title": "[BROM] Bypass SLA / DAA",
        "subtitle": "Contourne l'authentification SLA/DAA en mode BROM.",
        "explanation": "Bypasse l'authentification SLA (Secondary Loader Authentication) et DAA sur les processeurs MediaTek en mode BROM pour autoriser les opérations de flash.",
    },
    "FASTBOOT_GETVAR": {
        "title": "[FASTBOOT] Getvar All",
        "subtitle": "Lit les variables Fastboot de l'appareil.",
        "explanation": "Affiche toutes les variables Fastboot (version, serial, unlocked, etc.) de l'appareil connecté en mode Fastboot.",
    },
    "FASTBOOT_ERASE_USERDATA": {
        "title": "[FASTBOOT] Erase Userdata",
        "subtitle": "Efface la partition userdata en Fastboot.",
        "explanation": "Formate la partition userdata de l'appareil Android en mode Fastboot. Toutes les données utilisateur seront définitivement supprimées.",
    },
    "REBOOT_NORMAL": {
        "title": "[REBOOT] Redémarrage Normal",
        "subtitle": "Redémarre l'appareil en mode normal.",
        "explanation": "Redémarre l'appareil connecté vers le mode normal (Android).",
    },
    "REBOOT_FASTBOOT": {
        "title": "[REBOOT] Redémarrage Fastboot",
        "subtitle": "Redémarre l'appareil en mode Fastboot.",
        "explanation": "Redémarre l'appareil Android connecté (en mode ADB) vers le mode Fastboot.",
    },
    "REBOOT_RECOVERY": {
        "title": "[REBOOT] Redémarrage Recovery",
        "subtitle": "Redémarre l'appareil en mode Recovery.",
        "explanation": "Redémarre l'appareil connecté vers le mode Recovery pour les opérations de maintenance et de flash.",
    },
    "FASTBOOT_OEM_CLEAR": {
        "title": "[FASTBOOT] OEM Clear",
        "subtitle": "Efface les données OEM en mode Fastboot.",
        "explanation": "Exécute 'fastboot oem clear' pour effacer les données et verrous OEM de l'appareil en mode Fastboot.",
    },
    "RECOVERY_READ_INFO": {
        "title": "[RECOVERY] Lire Infos",
        "subtitle": "Lit les informations en mode Recovery.",
        "explanation": "Lit les informations de l'appareil Android connecté en mode Recovery ou ADB.",
    },
    "RECOVERY_FORMAT": {
        "title": "[RECOVERY] Format Data",
        "subtitle": "Formate la partition Data en Recovery.",
        "explanation": "Formate la partition Data de l'appareil en mode Recovery ou Fastboot. Toutes les données utilisateur seront supprimées.",
    },
}


# =====================================================================
# 1. En-tête des Marques (Top Bar)
# =====================================================================

class BrandTabBar(QFrame):
    """Barre supérieure horizontale compacte (44px) avec boutons de marque."""

    brand_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("brandTabBar")
        self.setFixedHeight(44)
        self._buttons: Dict[str, QPushButton] = {}
        self._active_brand = "MEDIATEK"

        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(6)

        lbl_logo = QLabel("OPTIMA MTK")
        lbl_logo.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_logo.setStyleSheet(f"color: {COLOR_ACCENT_BLUE}; letter-spacing: 0.8px; margin-right: 6px;")
        layout.addWidget(lbl_logo)

        for b in SUPPORTED_BRANDS:
            btn = QPushButton(f"{b['icon']} {b['name'].upper()}")
            btn.setObjectName("brandTabBtn")
            btn.setFixedHeight(34)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
            btn.setToolTip(b["desc"])
            btn.clicked.connect(lambda checked, b_id=b["id"]: self.select_brand(b_id))

            self._buttons[b["id"]] = btn
            layout.addWidget(btn)

        layout.addStretch()
        self._update_styles()

    def select_brand(self, brand_id: str, notify: bool = True):
        b_id = brand_id.upper()
        if b_id in self._buttons:
            self._active_brand = b_id
            self._update_styles()
            if notify:
                self.brand_changed.emit(b_id)

    def get_active_brand(self) -> str:
        return self._active_brand

    def _update_styles(self):
        for b_id, btn in self._buttons.items():
            if b_id == self._active_brand:
                btn.setStyleSheet(f"""
                    QPushButton#brandTabBtn {{
                        background-color: {COLOR_ACCENT_BLUE};
                        color: #ffffff;
                        border: 1px solid {COLOR_ACCENT_BLUE};
                        border-radius: 4px;
                        padding: 4px 12px;
                        font-weight: bold;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton#brandTabBtn {{
                        background-color: {COLOR_CARD_BG};
                        color: {COLOR_TEXT_MUTED};
                        border: 1px solid {COLOR_BORDER};
                        border-radius: 4px;
                        padding: 4px 10px;
                    }}
                    QPushButton#brandTabBtn:hover {{
                        background-color: {COLOR_CARD_HOVER};
                        color: #ffffff;
                        border-color: {COLOR_ACCENT_BLUE}88;
                    }}
                """)


# =====================================================================
# 2. Panneau de Gauche : Liste & Sélection des Modèles / Chipsets
# =====================================================================

class ModelSelectorPanel(QFrame):
    """Panneau gauche fluide avec recherche et liste dynamique de modèles."""

    model_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("modelSelectorPanel")
        self.setMinimumWidth(230)
        self.setMaximumWidth(300)
        self._current_brand = "MEDIATEK"
        self._models_list: List[Dict[str, Any]] = []
        self._selected_model: Optional[Dict[str, Any]] = None

        self._build_ui()
        self.load_brand("MEDIATEK")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # En-tête compact
        header_layout = QHBoxLayout()
        self.lbl_header = QLabel("MODÈLES & SOC")
        self.lbl_header.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.lbl_header.setStyleSheet(f"color: {COLOR_TEXT_BRIGHT}; letter-spacing: 0.5px;")

        self.lbl_brand_badge = QLabel("MEDIATEK")
        self.lbl_brand_badge.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.lbl_brand_badge.setStyleSheet(f"""
            background-color: {COLOR_ACCENT_BLUE}22;
            color: {COLOR_ACCENT_BLUE};
            border: 1px solid {COLOR_ACCENT_BLUE};
            border-radius: 3px;
            padding: 1px 6px;
        """)

        header_layout.addWidget(self.lbl_header)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_brand_badge)
        layout.addLayout(header_layout)

        # Barre de recherche rapide
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Filtrer (ex: Hot 11, MT6765)...")
        self.txt_search.setFixedHeight(30)
        self.txt_search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLOR_CARD_BG};
                color: #ffffff;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding-left: 8px;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border-color: {COLOR_ACCENT_BLUE};
            }}
        """)
        self.txt_search.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.txt_search)

        # Liste des modèles (layout dynamique)
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("modelsListWidget")
        self.list_widget.setStyleSheet(f"""
            QListWidget#modelsListWidget {{
                background-color: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 2px;
            }}
            QListWidget#modelsListWidget::item {{
                border-bottom: 1px solid {COLOR_BORDER}55;
                padding: 6px 4px;
                color: {COLOR_TEXT_BRIGHT};
            }}
            QListWidget#modelsListWidget::item:hover {{
                background-color: {COLOR_CARD_HOVER};
            }}
            QListWidget#modelsListWidget::item:selected {{
                background-color: #0c365b;
                border: 1px solid {COLOR_ACCENT_BLUE};
                color: #ffffff;
            }}
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget, stretch=1)

        # Carte d'info de la cible active (hauteur adaptative sans conteneur bloquant)
        self.card_selected = QFrame()
        self.card_selected.setObjectName("selectedModelCard")
        self.card_selected.setMinimumHeight(68)
        self.card_selected.setStyleSheet(f"""
            QFrame#selectedModelCard {{
                background-color: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-left: 3px solid {COLOR_SUCCESS};
                border-radius: 4px;
            }}
        """)
        card_layout = QVBoxLayout(self.card_selected)
        card_layout.setContentsMargins(10, 6, 10, 6)
        card_layout.setSpacing(2)

        lbl_target_title = QLabel("CIBLE SÉLECTIONNÉE :")
        lbl_target_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px; font-weight: bold;")

        self.lbl_target_model = QLabel("MediaTek Auto-Detect")
        self.lbl_target_model.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_target_model.setStyleSheet(f"color: {COLOR_SUCCESS};")

        self.lbl_target_chip = QLabel("SoC : MT6765 / MT6768 Universal")
        self.lbl_target_chip.setStyleSheet(f"color: {COLOR_CYAN}; font-size: 10px; font-weight: bold;")

        self.lbl_target_modes = QLabel("Méthodes : BROM • FASTBOOT • META • ADB")
        self.lbl_target_modes.setStyleSheet(f"color: #cbd5e1; font-size: 9px;")

        card_layout.addWidget(lbl_target_title)
        card_layout.addWidget(self.lbl_target_model)
        card_layout.addWidget(self.lbl_target_chip)
        card_layout.addWidget(self.lbl_target_modes)
        layout.addWidget(self.card_selected)

    def load_brand(self, brand_id: str):
        self._current_brand = brand_id
        self.lbl_brand_badge.setText(brand_id.upper())
        self.txt_search.clear()
        self._models_list = get_models_for_brand(brand_id)
        self._populate_list(self._models_list)

        if self._models_list:
            self._select_model(self._models_list[0])

    def _populate_list(self, models: List[Dict[str, Any]]):
        self.list_widget.clear()
        for m in models:
            item = QListWidgetItem()
            item.setText(f"{m['model']}\n  ⚡ {m['chipset']}")
            item.setData(Qt.UserRole, m)
            item.setSizeHint(QSize(200, 42))
            self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_search_changed(self, text: str):
        filtered = search_models(text, self._current_brand)
        self._populate_list(filtered)

    def _on_item_clicked(self, item: QListWidgetItem):
        model_data = item.data(Qt.UserRole)
        if model_data:
            self._select_model(model_data)

    def _select_model(self, model_data: Dict[str, Any]):
        self._selected_model = model_data
        self.lbl_target_model.setText(model_data["model"])
        self.lbl_target_chip.setText(f"SoC : {model_data.get('chipset', 'MTK Generic')}")
        modes_str = " • ".join(model_data.get("modes", ["BROM", "FASTBOOT", "ADB"]))
        self.lbl_target_modes.setText(f"Méthodes : {modes_str}")
        self.model_selected.emit(model_data)

    def get_selected_model(self) -> Optional[Dict[str, Any]]:
        return self._selected_model


# =====================================================================
# 3. Panneau Central : Boutons d'Action & Onglets de Fonctionnalités
# =====================================================================

class ActionButton(QPushButton):
    """Bouton d'action optimisé (hauteur min 44px, haut contraste, zéro texte masqué)."""

    action_hovered = pyqtSignal(str)

    def __init__(self, badge: str, title: str, subtitle: str, color_hex: str = COLOR_ACCENT_BLUE, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(44)
        self.setMaximumHeight(50)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.badge = badge
        self.title = title
        self.subtitle = subtitle
        self.color_hex = color_hex
        self.action_key = ""

        # Texte principal propre et très lisible
        self.setText(f"[{self.badge}]  {self.title}")
        self.setFont(QFont("Segoe UI", 10, QFont.Bold))

        # Infobulle détaillée depuis le dictionnaire ACTION_TOOLTIPS
        tip = ACTION_TOOLTIPS.get(self.badge, {})
        full_title = tip.get("title", f"[{self.badge}] {self.title}")
        full_subtitle = tip.get("subtitle", self.subtitle)
        explanation = tip.get("explanation", "")
        self.setToolTip(f"<b>{full_title}</b><br>{full_subtitle}<br><br><i>{explanation}</i>")

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #141a29;
                color: #ffffff;
                border: 1px solid {self.color_hex}88;
                border-left: 5px solid {self.color_hex};
                border-radius: 4px;
                padding: 4px 12px;
                text-align: left;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #1c253b;
                border-color: {self.color_hex};
                color: #ffffff;
            }}
            QPushButton:pressed {{
                background-color: {self.color_hex}44;
            }}
            QPushButton:disabled {{
                background-color: #0d111a;
                border-color: {COLOR_BORDER};
                color: {COLOR_TEXT_MUTED};
            }}
        """)

    def enterEvent(self, event):
        super().enterEvent(event)
        self.action_hovered.emit(self.action_key)

    def leaveEvent(self, event):
        super().leaveEvent(event)


class ActionTabsPanel(QFrame):
    """
    Panneau central avec les 5 onglets de fonctionnalités par catégorie :
    [SECURITY / FRP], [FUNCTION], [FASTBOOT], [RECOVERY], [META]
    Layout fluide, espacements propres, boutons toujours 100% visibles.
    """

    action_triggered = pyqtSignal(str, dict)
    action_hovered = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("actionTabsPanel")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(6)

        # En-tête de cible active compact (26px)
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(4, 0, 4, 0)
        self.lbl_active_target = QLabel("⚡ CIBLE ACTIVE : MEDIATEK AUTO-DETECT")
        self.lbl_active_target.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_active_target.setStyleSheet(f"color: {COLOR_CYAN}; letter-spacing: 0.5px;")

        self.lbl_mode_pill = QLabel("PRÊT")
        self.lbl_mode_pill.setFont(QFont("Segoe UI", 8, QFont.Bold))
        self.lbl_mode_pill.setStyleSheet(f"""
            background-color: {COLOR_SUCCESS}22;
            color: {COLOR_SUCCESS};
            border: 1px solid {COLOR_SUCCESS};
            border-radius: 3px;
            padding: 1px 8px;
        """)

        top_bar.addWidget(self.lbl_active_target)
        top_bar.addStretch()
        top_bar.addWidget(self.lbl_mode_pill)
        layout.addLayout(top_bar)

        # Onglets de catégories (TFT layout)
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("actionCategoryTabs")
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: {COLOR_PANEL_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 6px;
            }}
            QTabBar::tab {{
                background-color: {COLOR_CARD_BG};
                color: {COLOR_TEXT_MUTED};
                padding: 7px 14px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: bold;
                font-size: 10px;
                border: 1px solid {COLOR_BORDER};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {COLOR_PANEL_BG};
                color: {COLOR_ACCENT_BLUE};
                border-bottom: 2px solid {COLOR_ACCENT_BLUE};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {COLOR_CARD_HOVER};
                color: #ffffff;
            }}
        """)

        self._tab_grids: Dict[str, QGridLayout] = {}
        self._current_brand: str = "MEDIATEK"
        self._current_model: Optional[Dict[str, Any]] = None

        self.tab_widget.addTab(self._build_category_tab("SECURITY"), "🔒 SECURITY / FRP")
        self.tab_widget.addTab(self._build_category_tab("FUNCTION"), "⚙️ FUNCTION")
        self.tab_widget.addTab(self._build_category_tab("FASTBOOT"), "⚡ FASTBOOT")
        self.tab_widget.addTab(self._build_category_tab("RECOVERY"), "🛠️ RECOVERY")
        self.tab_widget.addTab(self._build_category_tab("META"), "🌐 META")

        layout.addWidget(self.tab_widget, stretch=1)

        # Initialisation par défaut avec les actions MediaTek
        self.load_brand_actions("MEDIATEK")

    def _build_category_tab(self, category_key: str) -> QWidget:
        """Construit un conteneur d'onglet fluide prêt à recevoir une grille dynamique de boutons."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        layout.addLayout(grid)
        layout.addStretch()

        self._tab_grids[category_key] = grid
        return w

    def load_brand_actions(self, brand_id: str, model_data: Optional[Dict[str, Any]] = None):
        """
        Met à jour dynamiquement tous les boutons d'actions et l'en-tête selon la marque et le modèle.
        Chaque marque reçoit ses fonctions dédiées (ex: Samsung *#0*#, Xiaomi Mi Account, Infinix MDM).
        """
        from core.brands_config import get_brand_actions, get_brand_badge, get_brand_icon, get_brand_description

        self._current_brand = (brand_id or "MEDIATEK").upper()
        if model_data is not None:
            self._current_model = model_data

        brand_actions = get_brand_actions(self._current_brand)
        brand_icon = get_brand_icon(self._current_brand)
        brand_badge = get_brand_badge(self._current_brand)

        # Reconstitution des boutons dans chaque catégorie
        for category, grid in self._tab_grids.items():
            # Supprimer les anciens widgets
            while grid.count() > 0:
                item = grid.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

            # Ajouter les boutons configurés pour cette marque
            actions_list = brand_actions.get(category, [])
            for idx, act in enumerate(actions_list):
                row = idx // 2
                col = idx % 2
                btn = ActionButton(
                    badge=act.get("badge", "BROM"),
                    title=act.get("title", "ACTION"),
                    subtitle=act.get("subtitle", ""),
                    color_hex=act.get("color", COLOR_ACCENT_BLUE)
                )
                btn.action_key = act["key"]
                btn.action_hovered.connect(self.action_hovered.emit)
                btn.clicked.connect(
                    lambda ch, k=act["key"]: self.action_triggered.emit(
                        k, {"brand": self._current_brand, "model": self._current_model}
                    )
                )
                grid.addWidget(btn, row, col)

        # Mise à jour du bandeau de cible active avec l'icône de la marque
        if self._current_model:
            model_name = self._current_model.get("model", self._current_brand)
            chip = self._current_model.get("chipset", "MTK")
            self.lbl_active_target.setText(f"{brand_icon} CIBLE ACTIVE : {model_name.upper()} ({chip})")
        else:
            self.lbl_active_target.setText(f"{brand_icon} CIBLE ACTIVE : {brand_badge} (AUTO-DETECT)")

        self.lbl_mode_pill.setText(brand_badge)
        self.lbl_mode_pill.setStyleSheet(f"""
            background-color: {COLOR_ACCENT_BLUE}22;
            color: {COLOR_ACCENT_BLUE};
            border: 1px solid {COLOR_ACCENT_BLUE};
            border-radius: 3px;
            padding: 1px 8px;
        """)

    def update_selected_model(self, model_data: Dict[str, Any]):
        brand = model_data.get("brand_id", self._current_brand)
        self.load_brand_actions(brand, model_data)


# =====================================================================
# 4. Panneau de Droite : Gestionnaire de Connexion USB en Temps Réel
# =====================================================================

class ConnectionManagerPanel(QFrame):
    """Panneau droit compact et fluide avec statut matériel en direct."""

    rescan_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("connectionManagerPanel")
        self.setMinimumWidth(240)
        self.setMaximumWidth(310)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # En-tête
        lbl_head = QLabel("LIAISONS & MATÉRIEL")
        lbl_head.setFont(QFont("Segoe UI", 9, QFont.Bold))
        lbl_head.setStyleSheet(f"color: {COLOR_TEXT_BRIGHT}; letter-spacing: 0.5px;")
        layout.addWidget(lbl_head)

        # ── 1. Voyants matériels en direct ───────────────────────────
        status_box = QFrame()
        status_box.setObjectName("hardwareStatusBox")
        status_box.setStyleSheet(f"""
            QFrame#hardwareStatusBox {{
                background-color: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
        """)
        s_layout = QVBoxLayout(status_box)
        s_layout.setContentsMargins(10, 8, 10, 8)
        s_layout.setSpacing(6)

        self.row_brom = self._create_status_row("MTK USB (BROM/VCOM)", "🔴 Déconnecté")
        self.row_fastboot = self._create_status_row("Android Fastboot", "🔴 Déconnecté")
        self.row_adb = self._create_status_row("Android ADB Debug", "🔴 Inactif")

        s_layout.addLayout(self.row_brom["layout"])
        s_layout.addLayout(self.row_fastboot["layout"])
        s_layout.addLayout(self.row_adb["layout"])
        layout.addWidget(status_box)

        # ── 2. Carte d'Appareil Détecté ──────────────────────────────
        self.card_device = QFrame()
        self.card_device.setObjectName("liveDeviceCard")
        self.card_device.setStyleSheet(f"""
            QFrame#liveDeviceCard {{
                background-color: {COLOR_CARD_BG};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
        """)
        d_layout = QVBoxLayout(self.card_device)
        d_layout.setContentsMargins(10, 8, 10, 8)
        d_layout.setSpacing(3)

        lbl_dev_title = QLabel("APPAREIL SYNCHRONISÉ :")
        lbl_dev_title.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 9px; font-weight: bold;")
        d_layout.addWidget(lbl_dev_title)

        self.lbl_dev_name = QLabel("Aucun appareil détecté")
        self.lbl_dev_name.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_dev_name.setStyleSheet(f"color: {COLOR_DANGER};")
        d_layout.addWidget(self.lbl_dev_name)

        self.lbl_dev_port = QLabel("Liaison : —")
        self.lbl_dev_port.setStyleSheet(f"color: {COLOR_CYAN}; font-size: 10px; font-weight: bold;")
        d_layout.addWidget(self.lbl_dev_port)

        self.lbl_dev_proto = QLabel("Protocole : Surveillance active")
        self.lbl_dev_proto.setStyleSheet(f"color: #cbd5e1; font-size: 9px;")
        d_layout.addWidget(self.lbl_dev_proto)
        layout.addWidget(self.card_device)

        # ── 3. Bouton Rescan USB ──────────────────────────────────────
        self.btn_rescan = QPushButton("🔄 FORCER SCAN USB")
        self.btn_rescan.setFixedHeight(34)
        self.btn_rescan.setCursor(Qt.PointingHandCursor)
        self.btn_rescan.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.btn_rescan.setStyleSheet(f"""
            QPushButton {{
                background-color: #172134;
                color: {COLOR_ACCENT_BLUE};
                border: 1px solid {COLOR_ACCENT_BLUE}88;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_ACCENT_BLUE};
                color: #ffffff;
            }}
        """)
        self.btn_rescan.clicked.connect(self.rescan_requested.emit)
        layout.addWidget(self.btn_rescan)

        # ── 4. Aide-mémoire d'atelier (Texte haut contraste dynamique) ──────────
        guide_box = QFrame()
        guide_box.setObjectName("guideBox")
        guide_box.setStyleSheet(f"""
            QFrame#guideBox {{
                background-color: #0b0f19;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
        """)
        self.guide_layout = QVBoxLayout(guide_box)
        self.guide_layout.setContentsMargins(8, 6, 8, 6)
        self.guide_layout.setSpacing(3)

        self.lbl_guide_title = QLabel("INSTRUCTIONS D'ATELIER (MEDIATEK) :")
        self.lbl_guide_title.setStyleSheet(f"color: {COLOR_WARNING}; font-size: 9px; font-weight: bold;")
        self.guide_layout.addWidget(self.lbl_guide_title)
        self._tip_labels: List[QLabel] = []

        # ── 5. Guide contextuel dynamique (survol des boutons d'action) ─────────
        self.ctx_guide_box = QFrame()
        self.ctx_guide_box.setObjectName("ctxGuideBox")
        self.ctx_guide_box.setStyleSheet(f"""
            QFrame#ctxGuideBox {{
                background-color: #0d1526;
                border: 1px solid {COLOR_ACCENT_BLUE}44;
                border-left: 3px solid {COLOR_ACCENT_BLUE};
                border-radius: 4px;
            }}
        """)
        self.ctx_guide_layout = QVBoxLayout(self.ctx_guide_box)
        self.ctx_guide_layout.setContentsMargins(8, 6, 8, 6)
        self.ctx_guide_layout.setSpacing(3)

        self.lbl_ctx_title = QLabel("GUIDE CONTEXTUEL :")
        self.lbl_ctx_title.setStyleSheet(f"color: {COLOR_ACCENT_BLUE}; font-size: 9px; font-weight: bold;")
        self.ctx_guide_layout.addWidget(self.lbl_ctx_title)

        self.lbl_ctx_guide = QLabel("Survolez un bouton d'action pour afficher la procédure d'atelier.")
        self.lbl_ctx_guide.setWordWrap(True)
        self.lbl_ctx_guide.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-style: italic;")
        self.ctx_guide_layout.addWidget(self.lbl_ctx_guide)

        layout.addWidget(guide_box)
        layout.addWidget(self.ctx_guide_box)
        layout.addStretch()

        # Chargement des instructions par défaut
        self.update_workshop_instructions("MEDIATEK")

    def update_workshop_instructions(self, brand_id: str, custom_tips: Optional[List[str]] = None):
        """Met à jour dynamiquement les conseils d'atelier selon la marque sélectionnée."""
        from core.brands_config import get_brand_instructions, get_brand_config
        tips = custom_tips or get_brand_instructions(brand_id)
        brand_name = get_brand_config(brand_id).get("name", brand_id)
        self.lbl_guide_title.setText(f"INSTRUCTIONS D'ATELIER ({brand_name.upper()}) :")

        for lbl in self._tip_labels:
            self.guide_layout.removeWidget(lbl)
            lbl.deleteLater()
        self._tip_labels.clear()

        for t in tips:
            lbl_tip = QLabel(t)
            lbl_tip.setWordWrap(True)
            lbl_tip.setStyleSheet("color: #cbd5e1; font-size: 10px;")
            self.guide_layout.addWidget(lbl_tip)
            self._tip_labels.append(lbl_tip)

    def _create_status_row(self, title: str, default_val: str) -> Dict[str, Any]:
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("color: #cbd5e1; font-size: 10px;")

        lbl_v = QLabel(default_val)
        lbl_v.setFont(QFont("Segoe UI", 9, QFont.Bold))
        lbl_v.setStyleSheet(f"color: {COLOR_DANGER};")

        h_layout.addWidget(lbl_t)
        h_layout.addStretch()
        h_layout.addWidget(lbl_v)

        return {"layout": h_layout, "title_lbl": lbl_t, "val_lbl": lbl_v}

    def show_contextual_guide(self, action_key: str, guide_text: str):
        """Affiche le guide d'atelier contextuel quand la souris survole un bouton d'action."""
        self.lbl_ctx_title.setText(f"GUIDE CONTEXTUEL : {action_key}")
        self.lbl_ctx_guide.setText(guide_text)
        self.lbl_ctx_guide.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 10px; font-weight: normal;")

    def update_connection_state(self, device: Optional[ConnectedDevice]):
        if device is None:
            self.row_brom["val_lbl"].setText("🔴 Déconnecté")
            self.row_brom["val_lbl"].setStyleSheet(f"color: {COLOR_DANGER}; font-weight: bold;")

            self.row_fastboot["val_lbl"].setText("🔴 Déconnecté")
            self.row_fastboot["val_lbl"].setStyleSheet(f"color: {COLOR_DANGER}; font-weight: bold;")

            self.row_adb["val_lbl"].setText("🔴 Inactif")
            self.row_adb["val_lbl"].setStyleSheet(f"color: {COLOR_DANGER}; font-weight: bold;")

            self.lbl_dev_name.setText("Aucun appareil détecté")
            self.lbl_dev_name.setStyleSheet(f"color: {COLOR_DANGER};")
            self.lbl_dev_port.setText("Liaison : —")
            self.lbl_dev_proto.setText("Protocole : Surveillance active")
            self.card_device.setStyleSheet(f"QFrame#liveDeviceCard {{ background-color: {COLOR_CARD_BG}; border: 1px solid {COLOR_BORDER}; border-radius: 4px; }}")

        else:
            loc = device.port or device.serial_number or device.identifier
            if device.mode == DeviceMode.BROM:
                self.row_brom["val_lbl"].setText(f"🟢 Actif ({device.port or 'VCOM'})")
                self.row_brom["val_lbl"].setStyleSheet(f"color: {COLOR_SUCCESS}; font-weight: bold;")
                self.row_fastboot["val_lbl"].setText("🔴 Déconnecté")
                self.row_fastboot["val_lbl"].setStyleSheet(f"color: {COLOR_DANGER};")
                self.row_adb["val_lbl"].setText("🔴 Inactif")
                self.row_adb["val_lbl"].setStyleSheet(f"color: {COLOR_DANGER};")

            elif device.mode == DeviceMode.FASTBOOT:
                self.row_brom["val_lbl"].setText("🔴 Déconnecté")
                self.row_brom["val_lbl"].setStyleSheet(f"color: {COLOR_DANGER};")
                self.row_fastboot["val_lbl"].setText(f"🟢 Prêt ({device.serial_number or 'USB'})")
                self.row_fastboot["val_lbl"].setStyleSheet(f"color: {COLOR_CYAN}; font-weight: bold;")
                self.row_adb["val_lbl"].setText("🔴 Inactif")
                self.row_adb["val_lbl"].setStyleSheet(f"color: {COLOR_DANGER};")

            elif device.mode == DeviceMode.ADB:
                self.row_brom["val_lbl"].setText("🔴 Déconnecté")
                self.row_brom["val_lbl"].setStyleSheet(f"color: {COLOR_DANGER};")
                self.row_fastboot["val_lbl"].setText("🔴 Déconnecté")
                self.row_fastboot["val_lbl"].setStyleSheet(f"color: {COLOR_DANGER};")
                self.row_adb["val_lbl"].setText(f"🟢 Actif ({device.serial_number or 'USB'})")
                self.row_adb["val_lbl"].setStyleSheet(f"color: {COLOR_SUCCESS}; font-weight: bold;")

            elif device.mode in (DeviceMode.USB_NORMAL, DeviceMode.NORMAL):
                self.row_brom["val_lbl"].setText("🔴 Déconnecté")
                self.row_fastboot["val_lbl"].setText("🔴 Déconnecté")
                det_str = str(getattr(device, "details", {})).lower()
                proto_str = (device.protocol or "").lower()
                if "unauthorized" in det_str or "non autorisé" in proto_str:
                    self.row_adb["val_lbl"].setText("🟡 Non autorisé (Valider écran)")
                else:
                    self.row_adb["val_lbl"].setText("🟡 Détecté (Débogage inactif)")
                self.row_adb["val_lbl"].setStyleSheet(f"color: {COLOR_WARNING}; font-weight: bold;")

            name = device.description or "Périphérique MediaTek"
            self.lbl_dev_name.setText(name)
            self.lbl_dev_name.setStyleSheet(f"color: {device.color}; font-weight: bold;")
            self.lbl_dev_port.setText(f"Liaison : {loc}")
            self.lbl_dev_proto.setText(f"Protocole : {device.protocol or device.mode_display}")

            border_c = COLOR_SUCCESS if device.mode != DeviceMode.USB_NORMAL else COLOR_WARNING
            self.card_device.setStyleSheet(f"""
                QFrame#liveDeviceCard {{
                    background-color: {COLOR_CARD_BG};
                    border: 1px solid {border_c};
                    border-left: 3px solid {border_c};
                    border-radius: 4px;
                }}
            """)

