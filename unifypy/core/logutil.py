#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Small logging helpers for library-level warnings."""

import logging

logger = logging.getLogger("unifypy")


def warn(msg: str) -> None:
    """Emit a warning via the unifypy logger, with print fallback.

    When neither the unifypy logger nor the root logger has handlers
    (typical CLI without logging config), fall back to print so the
    message is still visible.
    """
    if logger.handlers or logging.getLogger().handlers:
        logger.warning(msg)
    else:
        print(f"警告: {msg}")
