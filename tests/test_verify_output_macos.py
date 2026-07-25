#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for PyInstallerPlugin._verify_output macOS .app paths."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from unifypy.plugins.pyinstaller_plugin import PyInstallerPlugin


class _FakeConfig:
    def __init__(self, name, onefile=False, platform="macos", display_name=None):
        self._name = name
        self._onefile = onefile
        self.current_platform = platform
        self._display_name = display_name

    def get(self, key, default=None):
        if key == "name":
            return self._name
        if key == "display_name":
            return self._display_name
        return default

    def get_pyinstaller_config(self):
        return {"onefile": self._onefile}


class _FakeFileOps:
    def get_executable_extension(self):
        return ""


def _ctx(tmp_path, **kwargs):
    dist = tmp_path / "dist"
    dist.mkdir()
    return SimpleNamespace(
        config=_FakeConfig(**kwargs),
        dist_dir=dist,
        file_ops=_FakeFileOps(),
    )


def test_verify_macos_app_by_name(tmp_path):
    ctx = _ctx(tmp_path, name="MyApp", platform="macos")
    (ctx.dist_dir / "MyApp.app").mkdir()
    plugin = PyInstallerPlugin(context=None)
    plugin._verify_output(ctx)  # should not raise


def test_verify_macos_app_by_display_name(tmp_path):
    ctx = _ctx(
        tmp_path, name="myapp", platform="macos", display_name="My App"
    )
    (ctx.dist_dir / "My App.app").mkdir()
    plugin = PyInstallerPlugin(context=None)
    plugin._verify_output(ctx)


def test_verify_macos_missing_raises(tmp_path):
    ctx = _ctx(tmp_path, name="MyApp", platform="macos")
    plugin = PyInstallerPlugin(context=None)
    with pytest.raises(RuntimeError, match="不存在"):
        plugin._verify_output(ctx)


def test_verify_onefile(tmp_path):
    ctx = _ctx(tmp_path, name="MyApp", onefile=True, platform="linux")
    (ctx.dist_dir / "MyApp").write_text("x", encoding="utf-8")
    plugin = PyInstallerPlugin(context=None)
    plugin._verify_output(ctx)
