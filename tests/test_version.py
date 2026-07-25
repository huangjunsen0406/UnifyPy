#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for version single source."""

from pathlib import Path

from unifypy import __version__
from unifypy.core.version import get_version


def test_init_version_matches_pyproject():
    root = Path(__file__).resolve().parents[1]
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    # crude parse: version = "x.y.z" under [project]
    found = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("version") and "=" in line:
            found = line.split("=", 1)[1].strip().strip('"').strip("'")
            break
    assert found is not None
    assert __version__ == found


def test_get_version_returns_string():
    v = get_version()
    assert isinstance(v, str)
    assert v  # non-empty
    # Should match package __version__ when metadata unavailable or same
    assert v == __version__ or len(v.split(".")) >= 2
