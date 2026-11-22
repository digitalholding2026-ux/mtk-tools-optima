from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from src.adapters.usb.drivers import check_backend, check_drivers, open_installer_script


def _completed(stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


def test_check_backend_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "exists", lambda self: True)
    assert check_backend() is True


def test_check_backend_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "exists", lambda self: False)
    assert check_backend() is False


def test_check_drivers_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "exists", lambda self: True)
    with patch(
        "src.adapters.usb.drivers.subprocess.run",
        return_value=_completed("MTK_VCOM\nQUALCOMM_9008\n"),
    ) as run_mock:
        result = check_drivers()

    assert result == {"mtk_vcom": True, "qualcomm_9008": True, "libusb_backend": True}
    run_mock.assert_called_once()


def test_check_drivers_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "exists", lambda self: False)
    with patch(
        "src.adapters.usb.drivers.subprocess.run",
        return_value=_completed(""),
    ):
        result = check_drivers()

    assert result == {"mtk_vcom": False, "qualcomm_9008": False, "libusb_backend": False}


def test_check_drivers_query_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "exists", lambda self: False)
    with patch(
        "src.adapters.usb.drivers.subprocess.run",
        side_effect=FileNotFoundError("powershell"),
    ):
        result = check_drivers()

    assert result == {"mtk_vcom": False, "qualcomm_9008": False, "libusb_backend": False}


def test_open_installer_script_opens_explorer() -> None:
    with patch("src.adapters.usb.drivers.subprocess.Popen") as popen_mock:
        script = open_installer_script()

    assert script.is_file()
    assert script.name == "install_drivers.ps1"
    popen_mock.assert_called_once_with(["explorer", str(script)])