"""Journalisation structurée.

Séparation stricte imposée par docs/ARCHITECTURE.md :

* journaux applicatifs JSON dans ``<logs_dir>/optima.log`` ;
* sorties brutes des sous-processus dans ``<raw_dir>/*.raw``.

``get_raw_log_path`` ne crée jamais le fichier : il se contente de calculer le
chemin. Les répertoires configurés sont créés par ``load_config``.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.core.config import AppConfig

__all__ = [
    "BACKUP_COUNT",
    "LOG_FILENAME",
    "MAX_LOG_BYTES",
    "JsonFormatter",
    "get_raw_log_path",
    "setup_logging",
]

LOG_FILENAME = "optima.log"
MAX_LOG_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5

_UNSAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")

_managed_handlers: list[logging.Handler] = []
_raw_dir: Path = Path("logs/raw")


def _utc_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).isoformat().replace("+00:00", "Z")


class JsonFormatter(logging.Formatter):
    """Formateur JSON : timestamp_utc, level, event, operator, payload."""

    def format(self, record: logging.LogRecord) -> str:
        payload = getattr(record, "payload", None)
        if not isinstance(payload, dict):
            payload = {"value": payload}

        entry: dict[str, Any] = {
            "timestamp_utc": _utc_iso(record.created),
            "level": record.levelname,
            "event": getattr(record, "event", None) or record.getMessage(),
            "operator": getattr(record, "operator", None) or "unknown",
            "payload": payload,
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(entry, ensure_ascii=False, default=str)


def setup_logging(config: AppConfig) -> logging.Logger:
    """Installe le handler rotatif JSON (5 Mo × 5) et retourne le logger racine."""
    global _raw_dir

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    for handler in _managed_handlers:
        root.removeHandler(handler)
        handler.close()
    _managed_handlers.clear()

    config.logs_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        config.logs_dir / LOG_FILENAME,
        maxBytes=MAX_LOG_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonFormatter())
    root.addHandler(file_handler)
    _managed_handlers.append(file_handler)

    _raw_dir = config.raw_dir
    return root


def get_raw_log_path(operation_id: str) -> Path:
    """Retourne le chemin brut d'une opération, sans créer le fichier."""
    safe = _UNSAFE_FILENAME.sub("_", operation_id).strip("_") or "operation"
    return _raw_dir / f"{safe}.raw"