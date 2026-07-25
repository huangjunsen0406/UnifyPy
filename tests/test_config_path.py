#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for --config path resolution relative to project_dir."""

import json
from pathlib import Path

from unifypy.plugins.config_plugin import ConfigPlugin
from unifypy.core.config import ConfigManager


def test_resolve_config_path_relative_to_project_dir(tmp_path, monkeypatch):
    project = tmp_path / "proj"
    project.mkdir()
    (project / "main.py").write_text("print('hi')\n", encoding="utf-8")
    cfg = project / "build.json"
    cfg.write_text(
        json.dumps(
            {
                "name": "Demo",
                "version": "1.0.0",
                "entry": "main.py",
            }
        ),
        encoding="utf-8",
    )

    # cwd is elsewhere
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.chdir(other)

    resolved = ConfigPlugin._resolve_config_path("build.json", project)
    assert Path(resolved) == cfg.resolve()

    manager = ConfigManager(
        config_path=resolved,
        args={"project_dir": str(project)},
    )
    assert manager.get("name") == "Demo"


def test_resolve_config_path_absolute_unchanged(tmp_path):
    cfg = tmp_path / "abs.json"
    cfg.write_text("{}", encoding="utf-8")
    resolved = ConfigPlugin._resolve_config_path(str(cfg), tmp_path / "proj")
    assert Path(resolved) == cfg.resolve()


def test_resolve_config_path_none():
    assert ConfigPlugin._resolve_config_path(None, "/tmp") is None
