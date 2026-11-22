"""Détection USB strictement passive.

Aucun transfert, aucune écriture : uniquement ``usb.core.find`` et la lecture
des descripteurs.
"""

from __future__ import annotations

from typing import Any

import usb.core

from src.core.types import ChipsetType, ConnectionMode, DeviceInfo, OperationError

__all__ = ["detect_devices"]

MEDIATEK_VID = 0x0E8D
MEDIATEK_PIDS = frozenset({0x0003, 0x2000, 0x2001})
QUALCOMM_VID = 0x05C6
QUALCOMM_EDL_PID = 0x9008

_USB_ENUM_FAILED = "USB_ENUM_FAILED"


def _enum_error(exc: BaseException) -> OperationError:
    return OperationError(
        "Énumération USB impossible.",
        code=_USB_ENUM_FAILED,
        details={"error": str(exc)},
    )


def _classify(vid: int, pid: int) -> tuple[ChipsetType, ConnectionMode] | None:
    if vid == MEDIATEK_VID and pid in MEDIATEK_PIDS:
        return ChipsetType.MTK, ConnectionMode.PRELOADER
    if vid == QUALCOMM_VID and pid == QUALCOMM_EDL_PID:
        return ChipsetType.QUALCOMM, ConnectionMode.EDL_9008
    return None


def _optional_serial(device: Any) -> str | None:
    try:
        value = device.serial_number
    except (usb.core.USBError, AttributeError, NotImplementedError, ValueError):
        return None
    if value is None:
        return None
    return str(value)


def _describe(device: Any) -> DeviceInfo | None:
    try:
        vid = int(device.idVendor)
        pid = int(device.idProduct)
        bus = int(device.bus)
        address = int(device.address)
    except usb.core.USBError as exc:
        raise _enum_error(exc) from exc
    except (AttributeError, TypeError, ValueError) as exc:
        raise OperationError(
            "Descripteur USB illisible.",
            code=_USB_ENUM_FAILED,
            details={"error": str(exc)},
        ) from exc

    classification = _classify(vid, pid)
    if classification is None:
        return None

    chipset, mode = classification
    return DeviceInfo(
        chipset=chipset,
        connection_mode=mode,
        vid=vid,
        pid=pid,
        bus=bus,
        address=address,
        serial=_optional_serial(device),
    )


def detect_devices() -> list[DeviceInfo]:
    """Énumère les appareils MediaTek et Qualcomm branchés, sans aucune écriture."""
    try:
        candidates = usb.core.find(find_all=True)
    except usb.core.USBError as exc:
        raise _enum_error(exc) from exc

    if candidates is None:
        return []

    devices: list[DeviceInfo] = []
    try:
        for device in candidates:
            info = _describe(device)
            if info is not None:
                devices.append(info)
    except usb.core.USBError as exc:
        raise _enum_error(exc) from exc

    return devices