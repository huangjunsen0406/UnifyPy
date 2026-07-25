#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for SilentRunner defaults."""

import inspect

from unifypy.utils.command_runner import SilentRunner


def test_run_command_shell_default_is_false():
    sig = inspect.signature(SilentRunner.run_command)
    assert sig.parameters["shell"].default is False
