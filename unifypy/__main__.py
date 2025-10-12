#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""CLI entry for the `unifypy` command."""

from unifypy.cli.argument_parser import ArgumentParser
from unifypy.core.context import BuildContext
from unifypy.core.plugin import PluginManager
from unifypy.core.engine import Engine


def main() -> int:
    args = ArgumentParser.parse_arguments()

    # 检查是否是交互式配置模式
    if args.init:
        from unifypy.cli.interactive import InteractiveWizard

        # 运行交互式向导
        wizard = InteractiveWizard(args.project_dir)
        config_path = wizard.run()

        if config_path is None:
            # 用户取消了配置
            return 0

        # 询问是否立即构建
        from unifypy.cli.interactive.input_handlers import InputHandler
        if InputHandler.confirm("Start building now?", default=True):
            print()
            InputHandler.info("开始构建...\n")

            # 使用生成的配置文件进行构建
            args.config = str(config_path)
            args.clean = True  # 自动添加 --clean
        else:
            InputHandler.info(f"运行以下命令开始打包:")
            print(f"  unifypy {args.project_dir} --config {config_path} --clean")
            return 0

    # 正常的构建流程
    context = BuildContext(args)
    engine = Engine(context, PluginManager(context))
    engine.setup()
    return engine.run()


if __name__ == "__main__":
    raise SystemExit(main())
