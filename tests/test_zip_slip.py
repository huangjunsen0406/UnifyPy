#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for Zip Slip protection in ToolManager._safe_extract_zip."""

import io
import zipfile
from pathlib import Path

import pytest

from unifypy.utils.tool_manager import ToolManager


def _make_zip(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in entries:
            zf.writestr(name, data)
    buf.seek(0)
    return zipfile.ZipFile(buf, "r")


def test_safe_extract_rejects_parent_traversal(tmp_path):
    zf = _make_zip([("../evil.txt", b"pwned"), ("ok.txt", b"fine")])
    with pytest.raises(RuntimeError, match="Zip Slip"):
        ToolManager._safe_extract_zip(zf, tmp_path)
    assert not (tmp_path / "evil.txt").exists()


def test_safe_extract_allows_normal_paths(tmp_path):
    zf = _make_zip([("dir/ok.txt", b"fine"), ("root.txt", b"x")])
    ToolManager._safe_extract_zip(zf, tmp_path)
    assert (tmp_path / "dir" / "ok.txt").read_bytes() == b"fine"
    assert (tmp_path / "root.txt").read_bytes() == b"x"
