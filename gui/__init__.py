# -*- coding: utf-8 -*-
"""Package gui - Interface graphique de l'application Optima MTK Tool."""

import os
import sys

_gui_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_gui_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

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
