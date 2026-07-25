#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Smoke tests for module-split public imports."""

from unifypy.pyinstaller.config_builder import PyInstallerConfigBuilder
from unifypy.pyinstaller.options import (
    BOOLEAN_OPTIONS,
    LIST_OPTIONS,
    PYINSTALLER_OPTIONS,
)
from unifypy.utils.tool_manager import APPIMAGETOOL_ASSETS, ToolManager
from unifypy.utils.tool_assets import APPIMAGETOOL_ASSETS as ASSETS_FROM_MODULE
from unifypy.platforms.windows.iss_builder import (
    generate_iss_script,
    process_iss_template,
)


def test_config_builder_exports_constants():
    assert "onefile" in PyInstallerConfigBuilder.PYINSTALLER_OPTIONS
    assert "onefile" in BOOLEAN_OPTIONS
    assert "add_data" in LIST_OPTIONS
    assert PYINSTALLER_OPTIONS is PyInstallerConfigBuilder.PYINSTALLER_OPTIONS or (
        "onefile" in PYINSTALLER_OPTIONS
    )


def test_tool_manager_reexports_assets():
    assert APPIMAGETOOL_ASSETS is ASSETS_FROM_MODULE
    assert "x86_64" in APPIMAGETOOL_ASSETS
    assert ToolManager is not None


def test_iss_builder_generate_minimal(tmp_path):
    src = tmp_path / "App.exe"
    src.write_bytes(b"MZ")
    out = tmp_path / "setup.exe"
    content = generate_iss_script(
        app_config={"name": "App", "version": "1.0.0", "publisher": "P"},
        format_config={},
        source_path=src,
        output_path=out,
    )
    assert "[Setup]" in content
    assert "AppName=App" in content
