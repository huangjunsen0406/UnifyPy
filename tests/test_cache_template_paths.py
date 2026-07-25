#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for CacheManager package template path resolution."""

from pathlib import Path

from unifypy.utils.cache_manager import CacheManager
from unifypy.plugins import packaging_plugin


def test_package_template_paths_under_unifypy_templates():
    paths = CacheManager._package_template_paths()
    assert paths, "expected at least one template path"
    pkg_templates = Path(__file__).resolve().parents[1] / "unifypy" / "templates"
    for p in paths:
        assert isinstance(p, Path)
        assert p.parent == pkg_templates
        assert "project_dir" not in str(p)
        # Must not be under an arbitrary project layout like <cwd>/unifypy/templates
        # when resolved from package install; path is relative to unifypy package root.
        assert p.parts[-3:] == ("unifypy", "templates", p.name)


def test_package_template_paths_exist():
    paths = CacheManager._package_template_paths()
    names = {p.name for p in paths}
    assert "setup.iss.template" in names
    assert "ChineseSimplified.isl.template" in names
    for p in paths:
        assert p.exists(), f"package template missing: {p}"


def test_packaging_plugin_does_not_call_optimize_pyinstaller_build():
    source = Path(packaging_plugin.__file__).read_text(encoding="utf-8")
    assert "optimize_pyinstaller_build" not in source
