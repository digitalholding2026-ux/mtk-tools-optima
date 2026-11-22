from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from src.adapters.mtk.adapter import MediaTekAdapterStub
from src.adapters.qualcomm.adapter import QualcommAdapterStub
from src.core.types import ChipsetType, ConnectionMode, DeviceInfo

MTK_MESSAGE = "Module MediaTek — implémentation prévue au Prompt 3."
QUALCOMM_MESSAGE = "Module Qualcomm — implémentation prévue au Prompt 4."


def _device() -> DeviceInfo:
    return DeviceInfo(
        chipset=ChipsetType.MTK,
        connection_mode=ConnectionMode.PRELOADER,
        vid=0x0E8D,
        pid=0x2000,
        bus=1,
        address=2,
    )


def _assert_raises(call: Callable[[], Any], message: str) -> None:
    with pytest.raises(NotImplementedError) as excinfo:
        call()
    assert str(excinfo.value) == message


@pytest.mark.parametrize(
    ("stub", "message"),
    [
        (MediaTekAdapterStub(), MTK_MESSAGE),
        (QualcommAdapterStub(), QUALCOMM_MESSAGE),
    ],
)
def test_stub_methods_raise(stub: Any, message: str) -> None:
    device = _device()

    _assert_raises(stub.detect, message)
    _assert_raises(lambda: stub.read_info(device), message)
    _assert_raises(lambda: stub.flash_partition(device, "boot", Path("boot.img")), message)
    _assert_raises(lambda: stub.erase_frp(device, "proof"), message)


def test_stub_messages_are_distinct() -> None:
    assert MTK_MESSAGE != QUALCOMM_MESSAGE
    assert "Prompt 3" in MTK_MESSAGE
    assert "Prompt 4" in QUALCOMM_MESSAGE