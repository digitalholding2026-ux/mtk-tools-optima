from __future__ import annotations

from src.core.types import (
    ChipsetType,
    ConnectionMode,
    DeviceInfo,
    OperationError,
    OperationFailure,
    OperationResult,
    OperationStatus,
)


def test_enum_values() -> None:
    assert ChipsetType.MTK.value == "mtk"
    assert ChipsetType.QUALCOMM.value == "qualcomm"
    assert ChipsetType.UNKNOWN.value == "unknown"

    assert ConnectionMode.NORMAL.value == "normal"
    assert ConnectionMode.PRELOADER.value == "preloader"
    assert ConnectionMode.EDL_9008.value == "edl_9008"
    assert ConnectionMode.FASTBOOT.value == "fastboot"
    assert ConnectionMode.UNKNOWN.value == "unknown"

    assert OperationStatus.PENDING.value == "pending"
    assert OperationStatus.RUNNING.value == "running"
    assert OperationStatus.SUCCESS.value == "success"
    assert OperationStatus.FAILED.value == "failed"
    assert OperationStatus.CANCELLED.value == "cancelled"
    assert OperationStatus.REFUSED.value == "refused"


def test_device_info_key_and_dict() -> None:
    device = DeviceInfo(
        chipset=ChipsetType.MTK,
        connection_mode=ConnectionMode.PRELOADER,
        vid=0x0E8D,
        pid=0x2000,
        bus=1,
        address=2,
        serial="ABC",
        model="Test",
    )

    assert device.key == "0e8d:2000@1.2"

    data = device.as_dict()
    assert data["chipset"] == "mtk"
    assert data["connection_mode"] == "preloader"
    assert data["vid"] == 0x0E8D
    assert data["serial"] == "ABC"


def test_operation_result_and_error() -> None:
    error = OperationError(message="boom", status=OperationStatus.FAILED)
    result = OperationResult(
        operation="flash",
        status=OperationStatus.FAILED,
        message="boom",
        error=error,
    )

    assert result.ok is False
    assert result.finished is True
    assert result.error is error

    data = result.as_dict()
    assert data["status"] == "failed"
    assert data["error"]["message"] == "boom"
    assert data["error"]["status"] == "failed"


def test_operation_result_factories() -> None:
    pending = OperationResult.pending("flash")
    assert pending.status is OperationStatus.PENDING
    assert pending.finished is False

    ok = OperationResult.success("flash", message="ok")
    assert ok.ok is True
    assert ok.finished is True

    refused = OperationResult.failed(
        "erase_frp",
        "preuve manquante",
        status=OperationStatus.REFUSED,
    )
    assert refused.status is OperationStatus.REFUSED
    assert refused.error is not None
    assert refused.error.status is OperationStatus.REFUSED


def test_operation_failure_wraps_error() -> None:
    error = OperationError(
        message="boom",
        code="USB_ENUM_FAILED",
        detail="detail",
    )
    failure = OperationFailure(error)

    assert failure.error is error
    assert failure.code == "USB_ENUM_FAILED"
    assert failure.message == "boom"
    assert failure.detail == "detail"
    assert str(failure) == "boom [USB_ENUM_FAILED]"