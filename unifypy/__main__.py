#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""CLI entry for the `unifypy` command."""

from unifypy.cli.argument_parser import ArgumentParser
from unifypy.core.context import BuildContext
from unifypy.core.plugin import PluginManager
from unifypy.core.engine import Engine


def main() -> int:
    args = ArgumentParser.parse_arguments()
    context = BuildContext(args)
    engine = Engine(context, PluginManager(context))
    engine.setup()
    return engine.run()


if __name__ == "__main__":
    raise SystemExit(main())
