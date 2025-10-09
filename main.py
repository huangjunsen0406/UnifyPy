#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UnifyPy 2.0 - 插件式生命周期引擎入口。
main.py 仅负责解析参数并委托给 Engine。
"""

import os
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.cli.argument_parser import ArgumentParser
from src.core.context import BuildContext
from src.core.plugin import PluginManager
from src.core.engine import Engine


def main():
    args = ArgumentParser.parse_arguments()
    context = BuildContext(args)
    engine = Engine(context, PluginManager(context))
    engine.setup()
    return engine.run()


if __name__ == "__main__":
    sys.exit(main())
