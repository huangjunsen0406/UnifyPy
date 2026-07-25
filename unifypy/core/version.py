#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Version helpers — single source of truth for UnifyPy tool version."""

from typing import Optional


def get_version() -> str:
    """Return the installed UnifyPy version.

    Prefers importlib.metadata (installed package), then falls back to
    ``unifypy.__version__``.
    """
    version = _from_metadata()
    if version:
        return version

    try:
        from unifypy import __version__

        return __version__
    except Exception:
        return "0.0.0"


def _from_metadata() -> Optional[str]:
    try:
        from importlib import metadata
    except ImportError:  # pragma: no cover - Python < 3.8
        try:
            import importlib_metadata as metadata  # type: ignore
        except ImportError:
            return None

    try:
        return metadata.version("unifypy")
    except Exception:
        return None
