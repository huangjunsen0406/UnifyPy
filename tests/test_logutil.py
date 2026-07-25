#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for logutil helpers."""

import logging

from unifypy.core import logutil


def test_logutil_info_warn_error_debug_callable(caplog, capsys):
    with caplog.at_level(logging.DEBUG, logger="unifypy"):
        logutil.info("hello-info")
        logutil.warn("hello-warn")
        logutil.error("hello-error")
        logutil.debug("hello-debug")

    # Prefer logger capture when handlers exist (pytest); else print fallback
    text = " ".join(r.message for r in caplog.records) + capsys.readouterr().out
    assert "hello-info" in text or "hello-info" in capsys.readouterr().out
    # re-read may be empty; use combined
    combined = " ".join(r.getMessage() for r in caplog.records)
    out = capsys.readouterr().out
    blob = combined + out
    # At least warn/error always logged at those levels
    assert "hello-warn" in blob
    assert "hello-error" in blob


def test_logutil_print_fallback_without_handlers(monkeypatch, capsys):
    """When no handlers, fall back to print with Chinese prefixes for warn/error."""
    # Clear handlers on unifypy and root temporarily
    unifypy_logger = logging.getLogger("unifypy")
    root = logging.getLogger()
    old_u = list(unifypy_logger.handlers)
    old_r = list(root.handlers)
    try:
        unifypy_logger.handlers.clear()
        root.handlers.clear()
        logutil.info("plain-info")
        logutil.warn("plain-warn")
        logutil.error("plain-error")
        out = capsys.readouterr().out
        assert "plain-info" in out
        assert "警告: plain-warn" in out
        assert "错误: plain-error" in out
    finally:
        unifypy_logger.handlers[:] = old_u
        root.handlers[:] = old_r
