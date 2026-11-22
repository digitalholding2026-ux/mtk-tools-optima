from __future__ import annotations

import json
import logging
import logging.handlers
from pathlib import Path

from src.core.config import AppConfig
from src.core.logging import get_raw_log_path, setup_logging


def _config(logs_dir: Path) -> AppConfig:
    return AppConfig(
        mtkclient_path=Path("bin/mtkclient"),
        edl_path=Path("bin/edl"),
        logs_dir=logs_dir,
        raw_dir=logs_dir / "raw",
        db_path=logs_dir / "optima.db",
        theme="dark",
    )


def test_json_log_is_structured(tmp_path: Path) -> None:
    config = _config(tmp_path / "logs")
    logger = setup_logging(config)

    logger.info(
        "unit_event",
        extra={"event": "unit_event", "operator": "alice", "payload": {"n": 1}},
    )
    for handler in logger.handlers:
        handler.flush()

    path = config.logs_dir / "optima.log"
    lines = path.read_text(encoding="utf-8").splitlines()

    entry = json.loads(lines[-1])
    assert entry["event"] == "unit_event"
    assert entry["level"] == "INFO"
    assert entry["operator"] == "alice"
    assert entry["payload"] == {"n": 1}
    assert entry["timestamp_utc"].endswith("Z")


def test_log_rotation(tmp_path: Path) -> None:
    config = _config(tmp_path / "logs")
    logger = setup_logging(config)

    handler = next(
        item
        for item in logger.handlers
        if isinstance(item, logging.handlers.RotatingFileHandler)
    )
    handler.maxBytes = 200

    logger.info("first")
    logger.info("x" * 500, extra={"event": "big", "payload": {}})
    handler.flush()

    assert (config.logs_dir / "optima.log.1").exists()


def test_get_raw_log_path_does_not_create(tmp_path: Path) -> None:
    config = _config(tmp_path / "logs")
    setup_logging(config)

    path = get_raw_log_path("op-123")

    assert path == config.raw_dir / "op-123.raw"
    assert not path.exists()
    assert not path.parent.exists()


def test_default_log_file_contains_json() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config = _config(repo_root / "logs")
    logger = setup_logging(config)

    logger.info(
        "default_log_probe",
        extra={
            "event": "default_log_probe",
            "operator": "pytest",
            "payload": {"ok": True},
        },
    )
    for handler in logger.handlers:
        handler.flush()

    path = repo_root / "logs" / "optima.log"
    assert path.is_file()

    entry = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])
    assert entry["event"] == "default_log_probe"
    assert entry["payload"] == {"ok": True}