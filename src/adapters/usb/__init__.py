"""Détection USB passive."""

from src.adapters.usb.detector import detect_devices
from src.core.types import OperationError

__all__ = ["OperationError", "detect_devices"]