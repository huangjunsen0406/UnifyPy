#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for PackagerRegistry per-import loading and process_built_app Info.plist update."""

import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from unifypy.platforms.macos.post_processor import MacOSPostProcessor
from unifypy.platforms.registry import PackagerRegistry


def test_registry_loads_defaults():
    reg = PackagerRegistry()
    # All five should load in a normal checkout
    assert reg.is_format_supported("windows", "exe")
    assert reg.is_format_supported("macos", "dmg")
    assert reg.is_format_supported("linux", "deb")
    assert reg.is_format_supported("linux", "rpm")
    assert reg.is_format_supported("linux", "appimage")


def test_registry_continues_when_one_import_fails():
    """One ImportError must not prevent other packagers from registering."""
    real_import = importlib.import_module

    def fake_import(name, *args, **kwargs):
        if name == "unifypy.platforms.linux.rpm_packager":
            raise ImportError("simulated missing rpm_packager")
        return real_import(name, *args, **kwargs)

    with patch("importlib.import_module", side_effect=fake_import):
        with patch("unifypy.core.logutil.warn") as warn_mock:
            reg = PackagerRegistry()

    assert not reg.is_format_supported("linux", "rpm")
    assert reg.is_format_supported("linux", "deb")
    assert reg.is_format_supported("linux", "appimage")
    assert reg.is_format_supported("windows", "exe")
    assert reg.is_format_supported("macos", "dmg")
    assert warn_mock.called
    warn_msg = warn_mock.call_args[0][0]
    assert "linux/rpm" in warn_msg


def test_process_built_app_calls_update_info_plist(tmp_path):
    app_name = "MyApp"
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    app_path = dist_dir / f"{app_name}.app"
    (app_path / "Contents" / "Resources").mkdir(parents=True)

    processor = MacOSPostProcessor(
        info_plist_updater=MagicMock(),
        macos_codesigner=MagicMock(),
        pyinstaller_builder=MagicMock(),
        verbose=False,
    )
    config = SimpleNamespace(get=lambda key, default=None: None)

    with patch.object(processor, "is_macos", return_value=True), patch.object(
        processor, "_update_info_plist", return_value=True
    ) as update_mock, patch.object(processor, "_sign_app") as sign_mock:
        ok = processor.process_built_app(app_name, dist_dir, config, tmp_path)

    assert ok is True
    update_mock.assert_called_once_with(app_path, config)
    sign_mock.assert_called_once()


def test_process_built_app_continues_sign_when_plist_update_fails(tmp_path):
    app_name = "MyApp"
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    app_path = dist_dir / f"{app_name}.app"
    (app_path / "Contents" / "Resources").mkdir(parents=True)

    processor = MacOSPostProcessor(
        info_plist_updater=MagicMock(),
        macos_codesigner=MagicMock(),
        pyinstaller_builder=MagicMock(),
        verbose=False,
    )
    config = SimpleNamespace(get=lambda key, default=None: None)

    with patch.object(processor, "is_macos", return_value=True), patch.object(
        processor, "_update_info_plist", return_value=False
    ), patch.object(processor, "_sign_app") as sign_mock:
        ok = processor.process_built_app(app_name, dist_dir, config, tmp_path)

    assert ok is True
    sign_mock.assert_called_once_with(app_path, tmp_path)
