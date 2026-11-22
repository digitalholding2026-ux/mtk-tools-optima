from __future__ import annotations

from pathlib import Path

import pytest

from src.core.config import ConfigError, load_config


def test_load_valid_yaml(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
binaries:
  mtkclient_path: "bin/mtkclient"
  edl_path: "bin/edl"
paths:
  logs_dir: "logs"
  raw_dir: "logs/raw"
  db_path: "data/optima.db"
ui:
  theme: "light"
""",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.mtkclient_path == tmp_path / "bin" / "mtkclient"
    assert config.edl_path == tmp_path / "bin" / "edl"
    assert config.logs_dir == tmp_path / "logs"
    assert config.raw_dir == tmp_path / "logs" / "raw"
    assert config.db_path == tmp_path / "data" / "optima.db"
    assert config.theme == "light"

    assert (tmp_path / "logs").is_dir()
    assert (tmp_path / "logs" / "raw").is_dir()
    assert (tmp_path / "data").is_dir()


def test_malformed_yaml_raises(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("paths: [", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(config_file)


def test_invalid_section_type_raises(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text("binaries: 42\n", encoding="utf-8")

    with pytest.raises(ConfigError):
        load_config(config_file)


def test_missing_explicit_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_config(tmp_path / "missing.yaml")


def test_all_keys_commented_example_uses_defaults(tmp_path: Path) -> None:
    example = tmp_path / "config.yaml.example"
    example.write_text(
        """
# binaries:
#   mtkclient_path: "bin/mtkclient"
# paths:
#   logs_dir: "logs"
""",
        encoding="utf-8",
    )

    config = load_config(example)

    assert config.mtkclient_path == tmp_path / "bin" / "mtkclient"
    assert config.edl_path == tmp_path / "bin" / "edl"
    assert config.theme == "dark"
    assert (tmp_path / "logs").is_dir()