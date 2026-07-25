#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EnvironmentManager uses windows/macos/linux; internal_key keeps short prefixes."""

from unifypy.core.environment import EnvironmentManager
from unifypy.core.platforms import PLATFORM_LINUX, PLATFORM_MACOS, PLATFORM_WINDOWS


def test_current_platform_is_canonical(tmp_path):
    env = EnvironmentManager(str(tmp_path))
    assert env.current_platform in (
        PLATFORM_WINDOWS,
        PLATFORM_MACOS,
        PLATFORM_LINUX,
    )
    assert env.current_platform not in ("mac", "win")


def test_internal_key_uses_short_prefix(tmp_path):
    env = EnvironmentManager(str(tmp_path))
    short_prefix = {
        "windows": "win",
        "macos": "mac",
        "linux": "linux",
    }[env.current_platform]
    assert env.internal_key.startswith(short_prefix + "-")
    assert env.normalized_arch in ("x64", "arm64")
    # modern filename embeds short-form internal_key
    name = env.get_modern_filename("myapp", "1.0.0", "zip")
    assert short_prefix + "-" in name
