#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ToolManager should attach CacheManager to project_dir, not process cwd."""

from pathlib import Path

from unifypy.utils.tool_manager import ToolManager


def test_tool_manager_cache_uses_project_dir(tmp_path):
    project = tmp_path / "my_project"
    project.mkdir()

    tm = ToolManager(
        tools_dir=str(tmp_path / "tools"),
        allow_auto_install=False,
        project_dir=str(project),
    )

    assert tm.cache_manager.project_dir == project.resolve()


def test_tool_manager_cache_defaults_to_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    tm = ToolManager(
        tools_dir=str(tmp_path / "tools"),
        allow_auto_install=False,
    )

    assert tm.cache_manager.project_dir == Path.cwd().resolve()
