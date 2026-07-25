#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for ToolManager._download_file SHA256 verification."""

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from unifypy.utils.tool_manager import ToolManager


class _FakeResponse:
    def __init__(self, data: bytes):
        self._data = data

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size=8192):
        yield self._data


def test_download_rejects_bad_hash(tmp_path):
    tm = ToolManager(tools_dir=str(tmp_path / "tools"), allow_auto_install=False)
    target = tmp_path / "out.bin"
    payload = b"hello-world"

    with patch(
        "unifypy.utils.tool_download.requests.get",
        return_value=_FakeResponse(payload),
    ):
        with pytest.raises(RuntimeError, match="SHA256"):
            tm._download_file(
                "https://example.com/file",
                target,
                expected_sha256="0" * 64,
            )

    assert not target.exists()


def test_download_accepts_good_hash(tmp_path):
    tm = ToolManager(tools_dir=str(tmp_path / "tools"), allow_auto_install=False)
    target = tmp_path / "out.bin"
    payload = b"hello-world"
    digest = hashlib.sha256(payload).hexdigest()

    with patch(
        "unifypy.utils.tool_download.requests.get",
        return_value=_FakeResponse(payload),
    ):
        tm._download_file(
            "https://example.com/file",
            target,
            expected_sha256=digest,
        )

    assert target.read_bytes() == payload


def test_auto_install_enabled_by_default(tmp_path):
    """Default allow_auto_install is True (CI-friendly)."""
    tm = ToolManager(tools_dir=str(tmp_path / "tools"))
    assert tm.allow_auto_install is True


def test_auto_install_disabled_when_flag_false(tmp_path):
    tm = ToolManager(tools_dir=str(tmp_path / "tools"), allow_auto_install=False)
    assert tm.auto_install_tool("appimagetool") is False
    assert tm.auto_install_tool("dpkg-deb") is False
    assert tm.auto_install_tool("inno-setup") is False


def test_inno_never_auto_installs_even_when_allowed(tmp_path):
    tm = ToolManager(tools_dir=str(tmp_path / "tools"), allow_auto_install=True)
    assert tm.auto_install_tool("inno-setup") is False
