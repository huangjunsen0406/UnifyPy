#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for optional JSON Schema validation of build configs."""

import json
from pathlib import Path

import pytest

from unifypy.core.config import ConfigManager


def _write_config(tmp_path: Path, data: dict) -> str:
    path = tmp_path / "build.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


def test_schema_accepts_valid_minimal_config(tmp_path):
    entry = tmp_path / "main.py"
    entry.write_text("print('hi')\n", encoding="utf-8")
    cfg = {
        "name": "DemoApp",
        "version": "1.0.0",
        "entry": "main.py",
        "pyinstaller": {"onefile": True},
        "platforms": {"macos": {"formats": ["dmg"]}},
    }
    path = _write_config(tmp_path, cfg)
    cm = ConfigManager(
        config_path=path,
        args={"project_dir": str(tmp_path)},
    )
    assert cm.get("name") == "DemoApp"


def test_schema_rejects_name_as_number(tmp_path):
    entry = tmp_path / "main.py"
    entry.write_text("print('hi')\n", encoding="utf-8")
    cfg = {
        "name": 12345,
        "version": "1.0.0",
        "entry": "main.py",
    }
    path = _write_config(tmp_path, cfg)
    # Without jsonschema, validation is skipped; with it, ValueError
    jsonschema = pytest.importorskip("jsonschema")
    with pytest.raises(ValueError, match="JSON Schema|name"):
        ConfigManager(
            config_path=path,
            args={"project_dir": str(tmp_path)},
        )


def test_schema_rejects_pyinstaller_wrong_type(tmp_path):
    entry = tmp_path / "main.py"
    entry.write_text("print('hi')\n", encoding="utf-8")
    pytest.importorskip("jsonschema")
    cfg = {
        "name": "Demo",
        "entry": "main.py",
        "pyinstaller": "not-an-object",
    }
    path = _write_config(tmp_path, cfg)
    with pytest.raises(ValueError, match="JSON Schema|pyinstaller"):
        ConfigManager(
            config_path=path,
            args={"project_dir": str(tmp_path)},
        )
