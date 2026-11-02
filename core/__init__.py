# -*- coding: utf-8 -*-
"""Package core - Logique de communication USB/COM et scripts MTK."""

from core.init_env import (
    init_environment,
    get_libusb_backend,
    get_adb_path,
    get_fastboot_path,
    get_project_root,
    get_bin_dir,
    get_drivers_dir,
    get_data_dir,
    get_environment_diagnostics,
)
from core.actions import (
    read_device_info, factory_reset, factory_reset_adb, erase_frp, reboot_device,
    reboot_to_fastboot, unlock_bootloader, relock_bootloader,
    samsung_frp_testmode, samsung_read_info_mtp, bypass_mi_account,
    remove_mdm_payjoy, bypass_oppo_id, ActionResult
)
from core.brands_config import (
    BRANDS_CONFIG, get_brand_config, get_brand_actions,
    get_brand_instructions, get_brand_badge
)
from core.detector import (
    DeviceDetector, JITConnectionWorker, ConnectedDevice, DeviceMode,
    reset_adb_server, get_adb_path as get_detector_adb_path
)
from core.mtk_communication import MTKCommunication
from core.usb_reset import perform_hardware_wake, is_admin
from core.usb_scanner import UsbScanner, scan_mtk_devices, find_mtk_device, HAS_PYUSB

__all__ = [
    # Initialisation & Dépendances Bas-Niveau
    "init_environment",
    "get_libusb_backend",
    "get_adb_path",
    "get_fastboot_path",
    "get_project_root",
    "get_bin_dir",
    "get_drivers_dir",
    "get_data_dir",
    "get_environment_diagnostics",
    # Actions MTK
    "read_device_info",
    "factory_reset",
    "factory_reset_adb",
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
