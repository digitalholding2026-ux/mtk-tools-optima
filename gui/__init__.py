# -*- coding: utf-8 -*-
"""Package gui - Interface graphique de l'application Optima MTK Tool."""

import os
import sys

_gui_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_gui_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from .connection_assistant import ConnectionAssistantDialog, execute_with_assistant
from .main_window import MainWindow
from .device_info_tab import DeviceInfoTab
from .frp_tab import FRPResetTab
from .tools_tab import ToolsTab
from .log_panel import LogPanel
from .device_status_widget import DeviceStatusBanner
from .tft_widgets import (
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
