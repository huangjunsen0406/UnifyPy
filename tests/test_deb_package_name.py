#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for Debian package name validation."""

from unittest.mock import MagicMock, patch

from unifypy.platforms.linux.deb_packager import (
    DEBPackager,
    is_valid_deb_package_name,
)


def test_valid_deb_package_names():
    assert is_valid_deb_package_name("myapp")
    assert is_valid_deb_package_name("my-app")
    assert is_valid_deb_package_name("app1")
    assert is_valid_deb_package_name("a")
    assert is_valid_deb_package_name("foo+bar")
    assert is_valid_deb_package_name("libfoo1.0")
    assert is_valid_deb_package_name("python3-unifypy")


def test_invalid_deb_package_names():
    assert not is_valid_deb_package_name("")
    assert not is_valid_deb_package_name(None)  # type: ignore[arg-type]
    assert not is_valid_deb_package_name("MyApp")  # uppercase
    assert not is_valid_deb_package_name("-myapp")  # starts with hyphen
    assert not is_valid_deb_package_name(".myapp")  # starts with dot
    assert not is_valid_deb_package_name("my app")  # space
    assert not is_valid_deb_package_name("my_app")  # underscore
    assert not is_valid_deb_package_name("中文包")  # non-ascii


def _make_packager(config):
    with patch("unifypy.core.environment.EnvironmentManager"):
        return DEBPackager(
            progress_manager=MagicMock(),
            runner=MagicMock(),
            tool_manager=MagicMock(),
            config=config,
            project_dir=".",
        )


def test_validate_config_rejects_invalid_package_name():
    packager = _make_packager(
        {
            "name": "Bad_Name",
            "publisher": "Dev <dev@example.com>",
            "platforms": {"linux": {"deb": {}}},
        }
    )
    packager.get_format_config = lambda fmt: {}
    with patch("shutil.which", return_value="/usr/bin/dpkg-deb"):
        errors = packager.validate_config("deb")
    assert any("无效的 DEB 包名" in e for e in errors)


def test_validate_config_accepts_valid_package_field():
    packager = _make_packager(
        {
            "name": "My Display Name",
            "publisher": "Dev <dev@example.com>",
        }
    )
    packager.get_format_config = lambda fmt: {"package": "my-app"}
    with patch("shutil.which", return_value="/usr/bin/dpkg-deb"):
        errors = packager.validate_config("deb")
    assert not any("无效的 DEB 包名" in e for e in errors)
