from __future__ import annotations

import pytest
from PySide6.QtCore import Qt

from src.core.types import ChipsetType, ConnectionMode, DeviceInfo
from src.ui.main_window import MainWindow


def test_window_opens(qtbot, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.ui.main_window.check_backend", lambda: True)
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    assert window.windowTitle() == "Optima Telecom Flash Tool"
    assert window.isVisible()
    assert window.minimumWidth() >= 900
    assert window.minimumHeight() >= 600

    headers = [window._model.horizontalHeaderItem(i).text() for i in range(7)]
    assert headers == ["Chipset", "Mode", "VID", "PID", "Bus", "Adresse", "Série"]

    assert window._flash_button.isEnabled() is False
    assert window._frp_button.isEnabled() is False
    assert window._flash_button.toolTip() == "Disponible après implémentation du module métier"
    assert window._frp_button.toolTip() == "Disponible après implémentation du module métier"
    assert "Licence : OK (placeholder)" in window._status_label.text()
    assert "Backend USB : OK" in window._status_label.text()
    assert window._backend_banner.isHidden()
    assert window._scan_button.isEnabled()


def test_backend_missing_disables_scan(qtbot, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.ui.main_window.check_backend", lambda: False)
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    assert window._backend_banner.isVisible()
    assert "Backend libusb manquant" in window._backend_banner.text()
    assert not window._scan_button.isEnabled()
    assert "Backend USB : MANQUANT" in window._status_label.text()


def test_scan_populates_table_without_blocking(
    qtbot,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    device = DeviceInfo(
        chipset=ChipsetType.MTK,
        connection_mode=ConnectionMode.PRELOADER,
        vid=0x0E8D,
        pid=0x2000,
        bus=1,
        address=2,
        serial="SERIAL1",
    )
    monkeypatch.setattr("src.ui.main_window.check_backend", lambda: True)
    monkeypatch.setattr("src.ui.main_window.detect_devices", lambda: [device])

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    qtbot.mouseClick(window._scan_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window._model.rowCount() == 1 and window._scan_button.isEnabled(),
        timeout=3000,
    )

    assert window._model.item(0, 0).text() == "mtk"
    assert window._model.item(0, 1).text() == "preloader"
    assert window._model.item(0, 2).text() == "0x0E8D"
    assert window._model.item(0, 3).text() == "0x2000"
    assert window._model.item(0, 4).text() == "1"
    assert window._model.item(0, 5).text() == "2"
    assert window._model.item(0, 6).text() == "SERIAL1"
    assert window._scan_button.isEnabled()