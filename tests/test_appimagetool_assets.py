#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""APPIMAGETOOL_ASSETS must ship real SHA256 pins (fail-closed auto-install)."""

import re

from unifypy.utils.tool_manager import APPIMAGETOOL_ASSETS

_HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def test_appimagetool_assets_have_sha256_for_x86_64_and_aarch64():
    for arch in ("x86_64", "aarch64"):
        assert arch in APPIMAGETOOL_ASSETS
        sha = APPIMAGETOOL_ASSETS[arch].get("sha256")
        assert sha is not None, f"{arch} sha256 must not be None"
        assert isinstance(sha, str) and sha, f"{arch} sha256 must be non-empty"
        assert _HEX64.match(sha), f"{arch} sha256 must be 64 hex chars, got {sha!r}"


def test_appimagetool_arm64_shares_aarch64_pin():
    """arm64 aliases the aarch64 AppImage; hash must match."""
    assert "arm64" in APPIMAGETOOL_ASSETS
    arm = APPIMAGETOOL_ASSETS["arm64"]
    aarch = APPIMAGETOOL_ASSETS["aarch64"]
    assert arm.get("sha256") == aarch.get("sha256")
    assert arm.get("url") == aarch.get("url")
    assert _HEX64.match(arm["sha256"])
