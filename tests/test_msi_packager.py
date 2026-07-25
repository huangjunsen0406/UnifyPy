#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for MSI packager registry and WiX validation."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from unifypy.platforms.registry import PackagerRegistry
from unifypy.platforms.windows.msi_packager import MSIPackager, build_minimal_wxs


def test_registry_supports_msi():
    reg = PackagerRegistry()
    assert reg.is_format_supported("windows", "msi")
    assert reg.get_packager("windows", "msi") is MSIPackager


def test_validate_config_without_wix():
    progress = MagicMock()
    runner = MagicMock()
    tool_manager = MagicMock()
    config = {"name": "App", "version": "1.0.0"}
    packager = MSIPackager(
        progress, runner, tool_manager, config, project_dir="."
    )
    with patch(
        "unifypy.platforms.windows.msi_packager._wix_tools_available",
        return_value=False,
    ):
        errors = packager.validate_config("msi")
    assert errors
    assert any("WiX" in e for e in errors)


def test_can_package_format():
    packager = MSIPackager(MagicMock(), MagicMock(), MagicMock(), {}, project_dir=".")
    assert packager.can_package_format("msi")
    assert not packager.can_package_format("exe")


def test_build_minimal_wxs_contains_product(tmp_path):
    exe = tmp_path / "App.exe"
    exe.write_bytes(b"MZ")
    xml = build_minimal_wxs(
        product_name="App",
        version="1.0.0",
        manufacturer="Pub",
        upgrade_code="11111111-1111-1111-1111-111111111111",
        component_guid="22222222-2222-2222-2222-222222222222",
        source_file=exe,
        install_name="App.exe",
    )
    assert "Product" in xml
    assert "App.exe" in xml
    assert "ProgramFilesFolder" in xml


def test_default_formats_still_exe_only():
    from unifypy.core.formats import DEFAULT_FORMATS

    assert DEFAULT_FORMATS["windows"] == ["exe"]
