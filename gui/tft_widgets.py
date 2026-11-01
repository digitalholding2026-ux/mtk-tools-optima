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

    def select_brand(self, brand_id: str):
        if brand_id in self._buttons:
            self._active_brand = brand_id
            self._update_styles()
            self.brand_changed.emit(brand_id)

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

        self.lbl_target_modes = QLabel("Méthodes : BROM • FASTBOOT • META")
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
        modes_str = " • ".join(model_data.get("modes", ["BROM", "FASTBOOT"]))
        self.lbl_target_modes.setText(f"Méthodes : {modes_str}")
        self.model_selected.emit(model_data)

    def get_selected_model(self) -> Optional[Dict[str, Any]]:
        return self._selected_model


# =====================================================================
# 3. Panneau Central : Boutons d'Action & Onglets de Fonctionnalités
# =====================================================================

class ActionButton(QPushButton):
    """Bouton d'action optimisé (hauteur min 44px, haut contraste, zéro texte masqué)."""

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

        # Texte principal propre et très lisible
        self.setText(f"[{self.badge}]  {self.title}")
        self.setFont(QFont("Segoe UI", 10, QFont.Bold))
        # Infobulle détaillée sur le survol
        self.setToolTip(f"<b>[{self.badge}] {self.title}</b><br>{self.subtitle}")

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


class ActionTabsPanel(QFrame):
    """
    Panneau central avec les 5 onglets de fonctionnalités par catégorie :
    [SECURITY / FRP], [FUNCTION], [FASTBOOT], [RECOVERY], [META]
    Layout fluide, espacements propres, boutons toujours 100% visibles.
    """

    action_triggered = pyqtSignal(str, dict)

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

        self.tab_widget.addTab(self._build_tab_security(), "🔒 SECURITY / FRP")
        self.tab_widget.addTab(self._build_tab_function(), "⚙️ FUNCTION")
        self.tab_widget.addTab(self._build_tab_fastboot(), "⚡ FASTBOOT")
        self.tab_widget.addTab(self._build_tab_recovery(), "🛠️ RECOVERY")
        self.tab_widget.addTab(self._build_tab_meta(), "🌐 META")

        layout.addWidget(self.tab_widget, stretch=1)

    def _build_tab_security(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        btn_brom_frp = ActionButton("BROM", "ERASE FRP (Google Lock)", "Effacement partition persist matérielle", COLOR_SUCCESS)
        btn_brom_frp.clicked.connect(lambda: self.action_triggered.emit("BROM_ERASE_FRP", {}))

        btn_fastboot_frp = ActionButton("FASTBOOT", "ERASE FRP (OEM)", "Commandes fastboot erase frp/config", COLOR_CYAN)
        btn_fastboot_frp.clicked.connect(lambda: self.action_triggered.emit("FASTBOOT_ERASE_FRP", {}))

        btn_samsung_frp = ActionButton("BROM", "ERASE FRP (SAMSUNG)", "Déblocage Knox persistance Samsung MTK", COLOR_PURPLE)
        btn_samsung_frp.clicked.connect(lambda: self.action_triggered.emit("SAMSUNG_ERASE_FRP", {}))

        btn_unlock_bl = ActionButton("BROM", "UNLOCK BOOTLOADER", "Déverrouille le bootloader seccfg immédiatement", COLOR_WARNING)
        btn_unlock_bl.clicked.connect(lambda: self.action_triggered.emit("BROM_UNLOCK_BL", {}))

        btn_relock_bl = ActionButton("BROM", "RELOCK BOOTLOADER", "Reverrouille la sécurité bootloader", COLOR_TEXT_MUTED)
        btn_relock_bl.clicked.connect(lambda: self.action_triggered.emit("BROM_RELOCK_BL", {}))

        btn_oem_unlock = ActionButton("FASTBOOT", "OEM UNLOCK (BL)", "fastboot flashing unlock / oem unlock", COLOR_ACCENT_BLUE)
        btn_oem_unlock.clicked.connect(lambda: self.action_triggered.emit("FASTBOOT_OEM_UNLOCK", {}))

        grid.addWidget(btn_brom_frp, 0, 0)
        grid.addWidget(btn_fastboot_frp, 0, 1)
        grid.addWidget(btn_samsung_frp, 1, 0)
        grid.addWidget(btn_unlock_bl, 1, 1)
        grid.addWidget(btn_relock_bl, 2, 0)
        grid.addWidget(btn_oem_unlock, 2, 1)

        layout.addLayout(grid)
        layout.addStretch()
        return w

    def _build_tab_function(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        btn_reset = ActionButton("BROM", "FACTORY RESET (USERDATA)", "Formatage complet de la partition userdata", COLOR_DANGER)
        btn_reset.clicked.connect(lambda: self.action_triggered.emit("BROM_FACTORY_RESET", {}))

        btn_safe_format = ActionButton("BROM", "SAFE FORMAT (CACHE WIPE)", "Effacement sans supprimer les photos/données", COLOR_SUCCESS)
        btn_safe_format.clicked.connect(lambda: self.action_triggered.emit("BROM_SAFE_FORMAT", {}))

        btn_read_info = ActionButton("BROM", "READ DEVICE INFO (HW DUMP)", "Lecture hardware code, chip ID, MEID", COLOR_ACCENT_BLUE)
        btn_read_info.clicked.connect(lambda: self.action_triggered.emit("BROM_READ_INFO", {}))

        btn_remove_demo = ActionButton("BROM", "REMOVE DEMO / PAYJOY", "Suppression des restrictions de démonstration", COLOR_PURPLE)
        btn_remove_demo.clicked.connect(lambda: self.action_triggered.emit("BROM_REMOVE_DEMO", {}))

        btn_adb_info = ActionButton("ADB", "READ FULL SYSTEM SPECS", "Lecture version Android, build, IMEI via ADB", COLOR_CYAN)
        btn_adb_info.clicked.connect(lambda: self.action_triggered.emit("ADB_READ_INFO", {}))

        btn_auth_bypass = ActionButton("BROM", "DISABLE DAA / SLA (BYPASS)", "Désactive la signature de sécurité MediaTek", COLOR_WARNING)
        btn_auth_bypass.clicked.connect(lambda: self.action_triggered.emit("BROM_AUTH_BYPASS", {}))

        grid.addWidget(btn_reset, 0, 0)
        grid.addWidget(btn_safe_format, 0, 1)
        grid.addWidget(btn_read_info, 1, 0)
        grid.addWidget(btn_remove_demo, 1, 1)
        grid.addWidget(btn_adb_info, 2, 0)
        grid.addWidget(btn_auth_bypass, 2, 1)

        layout.addLayout(grid)
        layout.addStretch()
        return w

    def _build_tab_fastboot(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        btn_fb_info = ActionButton("FASTBOOT", "READ INFO (GETVAR ALL)", "Inspection des variables globales du bootloader", COLOR_CYAN)
        btn_fb_info.clicked.connect(lambda: self.action_triggered.emit("FASTBOOT_GETVAR", {}))

        btn_fb_wipe = ActionButton("FASTBOOT", "ERASE USERDATA", "fastboot erase userdata & cache", COLOR_DANGER)
        btn_fb_wipe.clicked.connect(lambda: self.action_triggered.emit("FASTBOOT_ERASE_USERDATA", {}))

        btn_fb_reboot = ActionButton("FASTBOOT", "REBOOT TO SYSTEM", "fastboot reboot", COLOR_SUCCESS)
        btn_fb_reboot.clicked.connect(lambda: self.action_triggered.emit("REBOOT_NORMAL", {}))

        btn_fb_rec = ActionButton("FASTBOOT", "REBOOT TO RECOVERY", "fastboot reboot recovery", COLOR_PURPLE)
        btn_fb_rec.clicked.connect(lambda: self.action_triggered.emit("REBOOT_RECOVERY", {}))

        btn_fb_bl = ActionButton("FASTBOOT", "REBOOT TO BOOTLOADER", "fastboot reboot-bootloader", COLOR_ACCENT_BLUE)
        btn_fb_bl.clicked.connect(lambda: self.action_triggered.emit("REBOOT_FASTBOOT", {}))

        btn_fb_oem = ActionButton("FASTBOOT", "OEM FB_MODE CLEAR", "Suppression des drapeaux fabricant", COLOR_WARNING)
        btn_fb_oem.clicked.connect(lambda: self.action_triggered.emit("FASTBOOT_OEM_CLEAR", {}))

        grid.addWidget(btn_fb_info, 0, 0)
        grid.addWidget(btn_fb_wipe, 0, 1)
        grid.addWidget(btn_fb_reboot, 1, 0)
        grid.addWidget(btn_fb_rec, 1, 1)
        grid.addWidget(btn_fb_bl, 2, 0)
        grid.addWidget(btn_fb_oem, 2, 1)

        layout.addLayout(grid)
        layout.addStretch()
        return w

    def _build_tab_recovery(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        btn_rec_info = ActionButton("RECOVERY", "READ RECOVERY SPECS", "Lecture statut sideload et OS version", COLOR_CYAN)
        btn_rec_info.clicked.connect(lambda: self.action_triggered.emit("RECOVERY_READ_INFO", {}))

        btn_rec_format = ActionButton("SIDELOAD", "FACTORY RESET / WIPE DATA", "Formatage via script de récupération", COLOR_DANGER)
        btn_rec_format.clicked.connect(lambda: self.action_triggered.emit("RECOVERY_FORMAT", {}))

        btn_rec_norm = ActionButton("RECOVERY", "REBOOT TO NORMAL SYSTEM", "Redémarrage propre dans Android", COLOR_SUCCESS)
        btn_rec_norm.clicked.connect(lambda: self.action_triggered.emit("REBOOT_NORMAL", {}))

        btn_rec_boot = ActionButton("RECOVERY", "REBOOT TO BOOTLOADER", "Redémarrage direct vers Fastboot", COLOR_ACCENT_BLUE)
        btn_rec_boot.clicked.connect(lambda: self.action_triggered.emit("REBOOT_FASTBOOT", {}))

        grid.addWidget(btn_rec_info, 0, 0)
        grid.addWidget(btn_rec_format, 0, 1)
        grid.addWidget(btn_rec_norm, 1, 0)
        grid.addWidget(btn_rec_boot, 1, 1)

        layout.addLayout(grid)
        layout.addStretch()
        return w

    def _build_tab_meta(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        btn_meta_info = ActionButton("META", "READ FACTORY INFO", "Lecture données d'usine, IMEI, Baseband", COLOR_PURPLE)
        btn_meta_info.clicked.connect(lambda: self.action_triggered.emit("META_READ_INFO", {}))

        btn_meta_reset = ActionButton("META", "FACTORY RESET (META)", "Remise à zéro sans perte de calibration", COLOR_DANGER)
        btn_meta_reset.clicked.connect(lambda: self.action_triggered.emit("META_FACTORY_RESET", {}))

        btn_meta_nv = ActionButton("META", "BACKUP NVRAM / NVDATA", "Sauvegarde de secours des partitions réseau", COLOR_WARNING)
        btn_meta_nv.clicked.connect(lambda: self.action_triggered.emit("META_BACKUP_NV", {}))

        btn_meta_reboot = ActionButton("META", "REBOOT TO NORMAL", "Sortie du mode Meta et redémarrage Android", COLOR_SUCCESS)
        btn_meta_reboot.clicked.connect(lambda: self.action_triggered.emit("META_REBOOT_NORMAL", {}))

        grid.addWidget(btn_meta_info, 0, 0)
        grid.addWidget(btn_meta_reset, 0, 1)
        grid.addWidget(btn_meta_nv, 1, 0)
        grid.addWidget(btn_meta_reboot, 1, 1)

        layout.addLayout(grid)
        layout.addStretch()
        return w

    def update_selected_model(self, model_data: Dict[str, Any]):
        name = model_data.get("model", "MediaTek Universal")
        chip = model_data.get("chipset", "")
        self.lbl_active_target.setText(f"⚡ CIBLE ACTIVE : {name.upper()} ({chip})")


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

        # ── 4. Aide-mémoire d'atelier (Texte haut contraste) ──────────
        guide_box = QFrame()
        guide_box.setObjectName("guideBox")
        guide_box.setStyleSheet(f"""
            QFrame#guideBox {{
                background-color: #0b0f19;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
            }}
        """)
        g_layout = QVBoxLayout(guide_box)
        g_layout.setContentsMargins(8, 6, 8, 6)
        g_layout.setSpacing(3)

        lbl_guide_title = QLabel("INSTRUCTIONS D'ATELIER :")
        lbl_guide_title.setStyleSheet(f"color: {COLOR_WARNING}; font-size: 9px; font-weight: bold;")
        g_layout.addWidget(lbl_guide_title)

        tips = [
            "• BROM MediaTek : Éteindre + Vol- + Câble",
            "• Fastboot Mode : Éteindre + Vol- & Power",
            "• Samsung MTK : Éteindre + Vol+ & Vol- + Câble",
            "• Pilotes requis : MediaTek USB VCOM Driver",
        ]
        for t in tips:
            lbl_tip = QLabel(t)
            lbl_tip.setWordWrap(True)
            lbl_tip.setStyleSheet("color: #cbd5e1; font-size: 10px;")
            g_layout.addWidget(lbl_tip)

        layout.addWidget(guide_box)
        layout.addStretch()

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
                self.row_adb["val_lbl"].setText("🟡 Non autorisé")
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
