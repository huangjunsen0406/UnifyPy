#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for macOS notarize helpers."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from unifypy.utils.macos_notarize import (
    can_notarize,
    credentials_ready,
    notarize_and_staple,
    resolve_notarize_credentials,
)


def test_can_notarize_false_when_xcrun_missing():
    with patch("unifypy.utils.macos_notarize.shutil.which", return_value=None):
        assert can_notarize() is False


def test_can_notarize_true_when_notarytool_help_ok():
    with patch("unifypy.utils.macos_notarize.shutil.which", return_value="/usr/bin/xcrun"):
        with patch("unifypy.utils.macos_notarize.subprocess.run") as run:
            run.return_value = MagicMock(returncode=0)
            assert can_notarize() is True


def test_resolve_credentials_from_env(monkeypatch):
    monkeypatch.setenv("UNIFYPY_APPLE_ID", "a@b.com")
    monkeypatch.setenv("UNIFYPY_TEAM_ID", "TEAM123")
    monkeypatch.setenv("UNIFYPY_APPLE_PASSWORD", "secret")
    creds = resolve_notarize_credentials({})
    assert credentials_ready(creds)
    assert creds["apple_id"] == "a@b.com"


def test_resolve_credentials_profile(monkeypatch):
    monkeypatch.delenv("UNIFYPY_APPLE_ID", raising=False)
    monkeypatch.setenv("UNIFYPY_NOTARY_PROFILE", "AC_PASSWORD")
    creds = resolve_notarize_credentials({})
    assert credentials_ready(creds)
    assert creds["profile"] == "AC_PASSWORD"


def test_notarize_and_staple_missing_creds(tmp_path):
    target = tmp_path / "app.dmg"
    target.write_bytes(b"x")
    with patch("unifypy.utils.macos_notarize.can_notarize", return_value=True):
        with pytest.raises(RuntimeError, match="凭据"):
            notarize_and_staple(target)


def test_notarize_and_staple_success(tmp_path):
    target = tmp_path / "app.dmg"
    target.write_bytes(b"x")
    progress = MagicMock()
    with patch("unifypy.utils.macos_notarize.can_notarize", return_value=True):
        with patch("unifypy.utils.macos_notarize.subprocess.run") as run:
            run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            ok = notarize_and_staple(
                target,
                profile="myprofile",
                progress=progress,
            )
    assert ok is True
    assert run.call_count == 2  # submit + staple
