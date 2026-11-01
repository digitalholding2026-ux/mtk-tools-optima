# -*- coding: utf-8 -*-
"""Package gui - Interface graphique de l'application Optima MTK Tool."""

from gui.connection_assistant import ConnectionAssistantDialog, execute_with_assistant
from gui.main_window import MainWindow
from gui.device_info_tab import DeviceInfoTab
from gui.frp_tab import FRPResetTab
from gui.tools_tab import ToolsTab
from gui.log_panel import LogPanel
from gui.device_status_widget import DeviceStatusBanner
from gui.tft_widgets import (
    BrandTabBar,
    ModelSelectorPanel,
    ActionTabsPanel,
    ConnectionManagerPanel,
)

__all__ = [
    "MainWindow",
    "BrandTabBar",
    "ModelSelectorPanel",
    "ActionTabsPanel",
    "ConnectionManagerPanel",
    "DeviceInfoTab",
    "FRPResetTab",
    "ToolsTab",
    "LogPanel",
    "DeviceStatusBanner",
    "ConnectionAssistantDialog",
    "execute_with_assistant",
]
