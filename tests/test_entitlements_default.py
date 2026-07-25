#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for macOS entitlements defaulting to production."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from unifypy.platforms.macos.post_processor import MacOSPostProcessor


def _processor():
    builder = MagicMock()
    builder.update_config_with_auto_entitlements.side_effect = (
        lambda raw, project_dir, development: {"development_flag": development}
    )
    pp = MacOSPostProcessor(
        info_plist_updater=MagicMock(),
        macos_codesigner=MagicMock(),
        pyinstaller_builder=builder,
        verbose=False,
    )
    # Force macos path without depending on host OS
    pp.is_macos = lambda: True
    return pp, builder


def test_default_is_production():
    pp, builder = _processor()
    args = SimpleNamespace(development=False, debug=False, production=False)
    config = SimpleNamespace(raw_config={})
    result = pp.prepare_entitlements_config(config, "/tmp", args)
    assert result["development_flag"] is False
    # ensure production flag alone does not invert (default already production)
    call_kwargs_dev = builder.update_config_with_auto_entitlements.call_args[0][2]
    assert call_kwargs_dev is False


def test_development_flag_enables():
    pp, builder = _processor()
    args = SimpleNamespace(development=True, debug=False, production=False)
    config = SimpleNamespace(raw_config={})
    result = pp.prepare_entitlements_config(config, "/tmp", args)
    assert result["development_flag"] is True


def test_debug_flag_enables():
    pp, builder = _processor()
    args = SimpleNamespace(development=False, debug=True, production=False)
    config = SimpleNamespace(raw_config={})
    result = pp.prepare_entitlements_config(config, "/tmp", args)
    assert result["development_flag"] is True


def test_production_flag_does_not_force_development():
    """Previously: development = not production or ...  (defaulted development)."""
    pp, builder = _processor()
    args = SimpleNamespace(development=False, debug=False, production=True)
    config = SimpleNamespace(raw_config={})
    result = pp.prepare_entitlements_config(config, "/tmp", args)
    assert result["development_flag"] is False
