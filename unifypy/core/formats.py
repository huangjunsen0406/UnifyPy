#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Format resolution helpers for packaging and environment checks.

Priority:
  1. CLI ``--format``
  2. Explicit ``platforms.<platform>.formats`` list
  3. Keys in platform config that are supported formats
  4. Platform defaults
"""

from typing import Any, Callable, Dict, List, Optional

DEFAULT_FORMATS = {
    "windows": ["exe"],
    "macos": ["dmg"],
    "linux": ["deb"],
}


def resolve_requested_formats(
    platform: str,
    *,
    cli_format: Optional[str] = None,
    platform_config: Optional[Dict[str, Any]] = None,
    is_format_supported: Optional[Callable[[str, str], bool]] = None,
) -> List[str]:
    """Resolve the list of packaging formats for a platform.

    Args:
        platform: Platform name (windows/macos/linux).
        cli_format: Explicit format from CLI ``--format``, if any.
        platform_config: ``platforms.<platform>`` config dict.
        is_format_supported: Optional ``(platform, key) -> bool`` used when
            scanning platform_config keys for supported formats.

    Returns:
        Ordered list of format names (may be empty).
    """
    if cli_format:
        return [cli_format]

    platform_config = platform_config or {}

    # Prefer explicit formats list
    if "formats" in platform_config:
        explicit = platform_config["formats"]
        if isinstance(explicit, list) and explicit:
            return list(explicit)

    # Fallback: scan keys that look like supported formats
    formats: List[str] = []
    if is_format_supported is not None:
        for key in platform_config.keys():
            if is_format_supported(platform, key):
                formats.append(key)

    if not formats:
        formats = list(DEFAULT_FORMATS.get(platform, []))

    return formats
