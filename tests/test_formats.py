#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for FormatResolver (resolve_requested_formats)."""

from unifypy.core.formats import DEFAULT_FORMATS, resolve_requested_formats


def test_cli_format_wins():
    result = resolve_requested_formats(
        "linux",
        cli_format="rpm",
        platform_config={"formats": ["deb"], "deb": {}},
    )
    assert result == ["rpm"]


def test_explicit_formats_list():
    result = resolve_requested_formats(
        "linux",
        platform_config={"formats": ["deb", "rpm"], "deb": {}, "rpm": {}},
    )
    assert result == ["deb", "rpm"]


def test_empty_formats_list_falls_through_to_key_scan():
    def is_supported(platform, key):
        return key in ("deb", "appimage")

    result = resolve_requested_formats(
        "linux",
        platform_config={"formats": [], "deb": {}, "rpm": {}, "appimage": {}},
        is_format_supported=is_supported,
    )
    assert result == ["deb", "appimage"]


def test_key_scan_with_mock_support():
    def is_supported(platform, key):
        return key == "dmg"

    result = resolve_requested_formats(
        "macos",
        platform_config={"dmg": {"volname": "App"}, "notes": "ignored"},
        is_format_supported=is_supported,
    )
    assert result == ["dmg"]


def test_defaults_when_empty_config():
    for platform, expected in DEFAULT_FORMATS.items():
        result = resolve_requested_formats(platform, platform_config={})
        assert result == expected


def test_defaults_when_no_supported_keys():
    def is_supported(platform, key):
        return False

    result = resolve_requested_formats(
        "windows",
        platform_config={"notes": "x", "other": {}},
        is_format_supported=is_supported,
    )
    assert result == ["exe"]


def test_unknown_platform_defaults_empty():
    result = resolve_requested_formats("freebsd", platform_config={})
    assert result == []
