#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for rebuild UX: pyinstaller -y and summary path selection."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from unifypy.plugins.pyinstaller_plugin import PyInstallerPlugin
from unifypy.plugins.summary_plugin import SummaryPlugin
from unifypy.utils.progress import ProgressManager


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
    dist.mkdir(exist_ok=True)
    return SimpleNamespace(
        config=_FakeConfig(**kwargs),
        dist_dir=dist,
        file_ops=_FakeFileOps(),
        installer_dir=tmp_path / "installer",
        args=SimpleNamespace(skip_exe=False, skip_installer=True),
        progress=None,
        runner=SimpleNamespace(last_stdout="", last_stderr=""),
    )


def test_build_pyinstaller_command_includes_noconfirm_flag():
    cmd = PyInstallerPlugin.build_pyinstaller_command(Path("app.spec"))
    assert cmd[0] == "pyinstaller"
    assert "-y" in cmd or "--noconfirm" in cmd
    assert "app.spec" in str(cmd[-1])


def test_pyinstaller_failure_non_empty_dir_mentions_clean():
    plugin = PyInstallerPlugin(context=None)
    runner = SimpleNamespace(
        last_stdout="",
        last_stderr="ERROR: The output directory is not empty. Please remove the output directory and try again.",
    )
    ctx = SimpleNamespace(runner=runner)
    err = plugin._pyinstaller_failure_error(ctx)
    assert isinstance(err, RuntimeError)
    msg = str(err)
    assert "--clean" in msg
    assert "upgrade" not in msg.lower()


def test_pyinstaller_failure_generic():
    plugin = PyInstallerPlugin(context=None)
    runner = SimpleNamespace(last_stdout="", last_stderr="some other error")
    ctx = SimpleNamespace(runner=runner)
    err = plugin._pyinstaller_failure_error(ctx)
    assert str(err) == "PyInstaller打包失败"


def test_summary_macos_prefers_display_name_app(tmp_path):
    ctx = _ctx(tmp_path, name="myapp", platform="macos", display_name="My App")
    # Junk tiny onedir leftover that used to be reported
    junk = ctx.dist_dir / "myapp"
    junk.mkdir()
    (junk / "marker").write_text("x", encoding="utf-8")
    app = ctx.dist_dir / "My App.app"
    app.mkdir()
    (app / "Contents").mkdir()
    (app / "Contents" / "MacOS").mkdir()
    (app / "Contents" / "MacOS" / "myapp").write_text("binary", encoding="utf-8")

    path = SummaryPlugin.resolve_executable_path(ctx)
    assert path is not None
    assert path.name == "My App.app"
    assert path.exists()


def test_summary_macos_falls_back_to_name_app(tmp_path):
    ctx = _ctx(tmp_path, name="MyApp", platform="macos")
    (ctx.dist_dir / "MyApp.app").mkdir()
    path = SummaryPlugin.resolve_executable_path(ctx)
    assert path is not None
    assert path.name == "MyApp.app"


def test_summary_macos_falls_back_to_onedir(tmp_path):
    ctx = _ctx(tmp_path, name="MyApp", platform="macos")
    (ctx.dist_dir / "MyApp").mkdir()
    path = SummaryPlugin.resolve_executable_path(ctx)
    assert path is not None
    assert path.name == "MyApp"
    assert not str(path).endswith(".app")


def test_summary_linux_onedir(tmp_path):
    ctx = _ctx(tmp_path, name="MyApp", platform="linux")
    (ctx.dist_dir / "MyApp").mkdir()
    path = SummaryPlugin.resolve_executable_path(ctx)
    assert path == ctx.dist_dir / "MyApp"


def test_summary_onefile(tmp_path):
    ctx = _ctx(tmp_path, name="MyApp", onefile=True, platform="linux")
    (ctx.dist_dir / "MyApp").write_text("bin", encoding="utf-8")
    path = SummaryPlugin.resolve_executable_path(ctx)
    assert path == ctx.dist_dir / "MyApp"


def test_error_suggestions_non_empty_dir_mentions_clean_not_upgrade():
    err = RuntimeError(
        "PyInstaller 打包失败：输出目录非空。"
        "请使用 `unifypy <project_dir> --clean` 清理后重试"
    )
    hints = ProgressManager.build_error_suggestions(err, "build_executable")
    joined = "\n".join(hints).lower()
    assert "--clean" in joined
    assert "upgrade" not in joined
    assert "升级" not in "\n".join(hints)


def test_error_suggestions_from_stderr_details_non_empty():
    err = Exception("命令执行失败 (返回码: 1)")
    details = (
        "ERROR: The output directory is not empty. "
        "Please remove the output directory and try again."
    )
    hints = ProgressManager.build_error_suggestions(
        err, "PyInstaller打包", details=details
    )
    joined = "\n".join(hints).lower()
    assert "--clean" in joined
    assert "upgrade" not in joined


def test_error_suggestions_generic_pyinstaller_still_mentions_upgrade():
    err = RuntimeError("PyInstaller打包失败")
    hints = ProgressManager.build_error_suggestions(err, "build_executable")
    joined = "\n".join(hints).lower()
    assert "upgrade" in joined or "升级" in "\n".join(hints)
