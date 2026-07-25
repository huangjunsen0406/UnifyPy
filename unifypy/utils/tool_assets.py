#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pinned third-party tool asset URLs and hashes."""

# Pinned appimagetool continuous-release assets + SHA256.
# Source: https://github.com/AppImage/appimagetool/releases/tag/continuous
#
# Continuous builds are mutable: when auto-install starts failing SHA256
# verification, re-download the AppImages and refresh the hashes below.
# Hashes recorded 2026-07-25.
APPIMAGETOOL_RELEASE = "continuous"  # tag segment used in URL path when overridden
APPIMAGETOOL_ASSETS = {
    "x86_64": {
        "url": (
            "https://github.com/AppImage/appimagetool/releases/download/"
            "continuous/appimagetool-x86_64.AppImage"
        ),
        "sha256": (
            "a6d71e2b6cd66f8e8d16c37ad164658985e0cf5fcaa950c90a482890cb9d13e0"
        ),
    },
    "aarch64": {
        "url": (
            "https://github.com/AppImage/appimagetool/releases/download/"
            "continuous/appimagetool-aarch64.AppImage"
        ),
        "sha256": (
            "1b00524ba8c6b678dc15ef88a5c25ec24def36cdfc7e3abb32ddcd068e8007fe"
        ),
    },
    # arm64 uses the same aarch64 AppImage asset.
    "arm64": {
        "url": (
            "https://github.com/AppImage/appimagetool/releases/download/"
            "continuous/appimagetool-aarch64.AppImage"
        ),
        "sha256": (
            "1b00524ba8c6b678dc15ef88a5c25ec24def36cdfc7e3abb32ddcd068e8007fe"
        ),
    },
}
