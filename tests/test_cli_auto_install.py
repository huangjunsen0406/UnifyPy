#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CLI defaults for --allow-auto-install / --no-allow-auto-install."""

import sys
from unittest.mock import patch

from unifypy.cli.argument_parser import ArgumentParser


def test_allow_auto_install_defaults_true():
    with patch.object(sys, "argv", ["unifypy", "."]):
        args = ArgumentParser.parse_arguments()
    assert args.allow_auto_install is True


def test_no_allow_auto_install_sets_false():
    with patch.object(sys, "argv", ["unifypy", ".", "--no-allow-auto-install"]):
        args = ArgumentParser.parse_arguments()
    assert args.allow_auto_install is False


def test_allow_auto_install_explicit_true():
    with patch.object(sys, "argv", ["unifypy", ".", "--allow-auto-install"]):
        args = ArgumentParser.parse_arguments()
    assert args.allow_auto_install is True
