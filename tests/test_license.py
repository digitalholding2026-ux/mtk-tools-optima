from __future__ import annotations

from unittest.mock import patch

from src.core.license import check_license


def test_check_license_returns_true() -> None:
    assert check_license() is True


def test_check_license_no_network() -> None:
    with (
        patch("socket.socket") as socket_mock,
        patch("socket.create_connection") as connect_mock,
        patch("socket.getaddrinfo") as dns_mock,
    ):
        assert check_license() is True

        socket_mock.assert_not_called()
        connect_mock.assert_not_called()
        dns_mock.assert_not_called()