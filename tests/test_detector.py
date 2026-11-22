from __future__ import annotations

from typing import Any

import pytest
import usb.core

from src.adapters.usb import detect_devices
from src.core.types import ChipsetType, ConnectionMode, DeviceInfo, OperationFailure


class FakeDevice:
    def __init__(
        self,
        vid: int,
        pid: int,
        bus: int = 1,
        address: int = 2,
        serial: str | None = None,
    ) -> None:
        self.idVendor = vid
        self.idProduct = pid
        self.bus = bus
        self.address = address
        self.serial_number = serial


def _find_with(devices: list[Any]):
    def finder(**_kwargs: Any) -> list[Any]:
        return devices

    return finder


def test_detect_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(usb.core, "find", _find_with([]))
    assert detect_devices() == []


def test_detect_mediaTek(monkeypatch: pytest.MonkeyPatch) -> None:
    device = FakeDevice(0x0E8D, 0x2000, bus=1, address=2, serial="MTK123")
    monkeypatch.setattr(usb.core, "find", _find_with([device]))

    assert detect_devices() == [
        DeviceInfo(
            chipset=ChipsetType.MTK,
            connection_mode=ConnectionMode.PRELOADER,
            vid=0x0E8D,
            pid=0x2000,
            bus=1,
            address=2,
            serial="MTK123",
        )
    ]


def test_detect_qualcomm(monkeypatch: pytest.MonkeyPatch) -> None:
    device = FakeDevice(0x05C6, 0x9008, bus=3, address=4, serial="QC456")
    monkeypatch.setattr(usb.core, "find", _find_with([device]))

    assert detect_devices() == [
        DeviceInfo(
            chipset=ChipsetType.QUALCOMM,
            connection_mode=ConnectionMode.EDL_9008,
            vid=0x05C6,
            pid=0x9008,
            bus=3,
            address=4,
            serial="QC456",
        )
    ]


def test_detect_filters_unsupported(monkeypatch: pytest.MonkeyPatch) -> None:
    devices = [
        FakeDevice(0x0E8D, 0x2000),
        FakeDevice(0x1234, 0x5678),
        FakeDevice(0x05C6, 0x9008),
    ]
    monkeypatch.setattr(usb.core, "find", _find_with(devices))

    detected = detect_devices()

    assert [item.chipset for item in detected] == [ChipsetType.MTK, ChipsetType.QUALCOMM]


def test_usb_error_raises_operation_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(**_kwargs: Any) -> None:
        raise usb.core.USBError("boom")

    monkeypatch.setattr(usb.core, "find", boom)

    with pytest.raises(OperationFailure) as excinfo:
        detect_devices()

    assert excinfo.value.error.code == "USB_ENUM_FAILED"


def test_no_backend_raises_operation_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(**_kwargs: Any) -> None:
        raise usb.core.NoBackendError("No backend available")

    monkeypatch.setattr(usb.core, "find", boom)

    with pytest.raises(OperationFailure) as excinfo:
        detect_devices()

    assert excinfo.value.error.code == "USB_BACKEND_MISSING"
    assert "libusb-1.0.dll" in excinfo.value.error.message
    assert excinfo.value.error.detail == "No backend available"


def test_serial_unavailable_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    class NoSerial:
        idVendor = 0x0E8D
        idProduct = 0x0003
        bus = 1
        address = 2

        @property
        def serial_number(self) -> str:
            raise usb.core.USBError("no serial")

    monkeypatch.setattr(usb.core, "find", _find_with([NoSerial()]))

    detected = detect_devices()

    assert len(detected) == 1
    assert detected[0].serial is None