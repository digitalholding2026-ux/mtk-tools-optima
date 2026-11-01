# -*- coding: utf-8 -*-
"""Package core - Logique de communication USB/COM et scripts MTK."""

from core.actions import (
    read_device_info, factory_reset, erase_frp, reboot_device,
    reboot_to_fastboot, unlock_bootloader, relock_bootloader, ActionResult
)
from core.detector import DeviceDetector, JITConnectionWorker, ConnectedDevice, DeviceMode, reset_adb_server
from core.mtk_communication import MTKCommunication
from core.usb_reset import perform_hardware_wake, is_admin
from core.usb_scanner import UsbScanner, scan_mtk_devices, find_mtk_device, HAS_PYUSB

__all__ = [
    # Actions MTK
    "read_device_info",
    "factory_reset",
    "erase_frp",
    "reboot_device",
    "reboot_to_fastboot",
    "unlock_bootloader",
    "relock_bootloader",
    "ActionResult",
    # Détection
    "DeviceDetector",
    "JITConnectionWorker",
    "ConnectedDevice",
    "DeviceMode",
    "MTKCommunication",
    "reset_adb_server",
    # USB bas-niveau (PyUSB)
    "UsbScanner",
    "scan_mtk_devices",
    "find_mtk_device",
    "HAS_PYUSB",
    # Initialisation système
    "perform_hardware_wake",
    "is_admin",
]
