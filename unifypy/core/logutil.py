#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Small logging helpers for library-level messages without full logging setup."""

import logging
from typing import Optional

logger = logging.getLogger("unifypy")

_schema_missing_warned = False


def _has_handlers() -> bool:
    return bool(logger.handlers or logging.getLogger().handlers)


def info(msg: str) -> None:
    """Emit an info message via the unifypy logger, with print fallback."""
    if _has_handlers():
        logger.info(msg)
    else:
        print(msg)


def warn(msg: str) -> None:
    """Emit a warning via the unifypy logger, with print fallback.

    When neither the unifypy logger nor the root logger has handlers
    (typical CLI without logging config), fall back to print so the
    message is still visible.
    """
    if _has_handlers():
        logger.warning(msg)
    else:
        print(f"警告: {msg}")


def error(msg: str) -> None:
    """Emit an error message via the unifypy logger, with print fallback."""
    if _has_handlers():
        logger.error(msg)
    else:
        print(f"错误: {msg}")


def debug(msg: str) -> None:
    """Emit a debug message via the unifypy logger, with print fallback."""
    if _has_handlers():
        logger.debug(msg)
    else:
        print(f"调试: {msg}")


def warn_once_schema_missing(msg: Optional[str] = None) -> None:
    """Warn once when optional jsonschema is not installed."""
    global _schema_missing_warned
    if _schema_missing_warned:
        return
    _schema_missing_warned = True
    warn(
        msg
        or "未安装 jsonschema，跳过配置 JSON Schema 校验（可选: pip install unifypy[schema]）"
    )
