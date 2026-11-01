# -*- coding: utf-8 -*-
"""
Module de compatibilité pour l'ancien com_detector.
Redirige vers la nouvelle implémentation core.detector.DeviceDetector.
"""

from core.detector import (
    DeviceDetector,
    DeviceMode,
    ConnectedDevice,
    MTK_VENDORS,
    MTK_BROM_PIDS,
    MTK_PRELOADER_PIDS,
    MTK_NORMAL_PIDS
)

# Alias direct pour conserver la compatibilité ascendante
COMDetector = DeviceDetector

__all__ = [
    "DeviceDetector",
    "COMDetector",
    "DeviceMode",
    "ConnectedDevice",
    "MTK_VENDORS",
    "MTK_BROM_PIDS",
    "MTK_PRELOADER_PIDS",
    "MTK_NORMAL_PIDS",
]
