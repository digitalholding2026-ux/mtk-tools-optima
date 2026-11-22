"""Types du cœur applicatif.

Ce module est purement descriptif : aucun import de `usb`, aucune dépendance
GPL, aucune écriture disque.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

__all__ = [
    "ChipsetType",
    "ConnectionMode",
    "DeviceInfo",
    "OperationError",
    "OperationFailure",
    "OperationResult",
    "OperationStatus",
]


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ChipsetType(StrEnum):
    """Fabricant de la plateforme détectée (SPEC F1)."""

    MTK = "mtk"
    QUALCOMM = "qualcomm"
    UNKNOWN = "unknown"


class ConnectionMode(StrEnum):
    """Mode de connexion de l'appareil (SPEC F1)."""

    NORMAL = "normal"
    PRELOADER = "preloader"
    EDL_9008 = "edl_9008"
    FASTBOOT = "fastboot"
    UNKNOWN = "unknown"


class OperationStatus(StrEnum):
    """Statut d'une opération (SPEC F3/F4/F5)."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUSED = "refused"


_TERMINAL_STATUSES = frozenset(
    {
        OperationStatus.SUCCESS,
        OperationStatus.FAILED,
        OperationStatus.CANCELLED,
        OperationStatus.REFUSED,
    }
)


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    """Description d'un appareil (F1) et de sa lecture non destructive (F2)."""

    chipset: ChipsetType
    connection_mode: ConnectionMode
    vid: int
    pid: int
    bus: int
    address: int
    serial: str | None = None
    model: str | None = None
    platform: str | None = None
    bootloader_state: str | None = None
    firmware_version: str | None = None
    partitions: tuple[str, ...] = ()
    info_reliable: bool = False

    @property
    def key(self) -> str:
        """Identifiant court et stable pour les journaux et l'interface."""
        return f"{self.vid:04x}:{self.pid:04x}@{self.bus}.{self.address}"

    def as_dict(self) -> dict[str, Any]:
        return {
            "chipset": self.chipset.value,
            "connection_mode": self.connection_mode.value,
            "vid": self.vid,
            "pid": self.pid,
            "bus": self.bus,
            "address": self.address,
            "serial": self.serial,
            "model": self.model,
            "platform": self.platform,
            "bootloader_state": self.bootloader_state,
            "firmware_version": self.firmware_version,
            "partitions": list(self.partitions),
            "info_reliable": self.info_reliable,
            "key": self.key,
        }


@dataclass(frozen=True)
class OperationError:
    """Erreur métier typée, sérialisable (valeur, non exception)."""

    message: str
    code: str = "INTERNAL_ERROR"
    status: OperationStatus = OperationStatus.FAILED
    device_key: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)
    detail: str | None = None

    @property
    def is_terminal(self) -> bool:
        return self.status in _TERMINAL_STATUSES

    def as_dict(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "code": self.code,
            "status": self.status.value,
            "device_key": self.device_key,
            "details": dict(self.details),
            "detail": self.detail,
        }


class OperationFailure(Exception):
    """Exception transportant une OperationError."""

    def __init__(self, error: OperationError) -> None:
        super().__init__(error.message)
        self.error = error

    @property
    def code(self) -> str:
        return self.error.code

    @property
    def message(self) -> str:
        return self.error.message

    @property
    def detail(self) -> str | None:
        return self.error.detail

    def __str__(self) -> str:
        return f"{self.error.message} [{self.error.code}]"


@dataclass(frozen=True, slots=True)
class OperationResult:
    """Résultat typé d'une opération, de son statut initial à son statut final."""

    operation: str
    status: OperationStatus = OperationStatus.PENDING
    device_key: str | None = None
    message: str = ""
    error: OperationError | None = None
    started_at: datetime = field(default_factory=_utcnow)
    finished_at: datetime | None = None
    duration_ms: int = 0
    details: Mapping[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status is OperationStatus.SUCCESS

    @property
    def finished(self) -> bool:
        return self.status in _TERMINAL_STATUSES

    @classmethod
    def pending(cls, operation: str, *, device_key: str | None = None) -> OperationResult:
        return cls(operation=operation, status=OperationStatus.PENDING, device_key=device_key)

    @classmethod
    def running(cls, operation: str, *, device_key: str | None = None) -> OperationResult:
        return cls(operation=operation, status=OperationStatus.RUNNING, device_key=device_key)

    @classmethod
    def success(
        cls,
        operation: str,
        *,
        device_key: str | None = None,
        message: str = "",
        details: Mapping[str, Any] | None = None,
    ) -> OperationResult:
        now = _utcnow()
        return cls(
            operation=operation,
            status=OperationStatus.SUCCESS,
            device_key=device_key,
            message=message,
            started_at=now,
            finished_at=now,
            details=dict(details or {}),
        )

    @classmethod
    def failed(
        cls,
        operation: str,
        message: str,
        *,
        device_key: str | None = None,
        status: OperationStatus = OperationStatus.FAILED,
        details: Mapping[str, Any] | None = None,
    ) -> OperationResult:
        now = _utcnow()
        payload = dict(details or {})
        error = OperationError(
            message=message,
            status=status,
            device_key=device_key,
            details=payload,
        )
        return cls(
            operation=operation,
            status=status,
            device_key=device_key,
            message=message,
            error=error,
            started_at=now,
            finished_at=now,
            details=payload,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "status": self.status.value,
            "device_key": self.device_key,
            "message": self.message,
            "error": None if self.error is None else self.error.as_dict(),
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at is not None else None,
            "duration_ms": self.duration_ms,
            "details": dict(self.details),
        }