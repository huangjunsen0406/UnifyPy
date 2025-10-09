#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
命令行参数解析器
负责解析和验证命令行参数
"""

import argparse
from typing import Any


class ArgumentParser:
    """
    UnifyPy 命令行参数解析器.
    """

    @staticmethod
    def parse_arguments() -> Any:
        """
        解析命令行参数.

        Returns:
            argparse.Namespace: 解析后的参数对象
        """
        parser = argparse.ArgumentParser(
            description="UnifyPy 2.0 - 跨平台Python应用打包工具",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例用法:
  python main.py . --config build.json
  python main.py /path/to/project --name myapp --version 1.0.0
  python main.py . --config build.json --verbose
            """,
        )

        # ========== 基本参数 ==========
        ArgumentParser._add_basic_arguments(parser)

        # ========== 文件和资源参数 ==========
        ArgumentParser._add_resource_arguments(parser)

        # ========== PyInstaller 选项 ==========
        ArgumentParser._add_pyinstaller_arguments(parser)

        # ========== 构建选项 ==========
        ArgumentParser._add_build_arguments(parser)

        # ========== 输出控制 ==========
        ArgumentParser._add_output_arguments(parser)

        # ========== 平台选项 ==========
        ArgumentParser._add_platform_arguments(parser)

        # ========== 性能选项 ==========
        ArgumentParser._add_performance_arguments(parser)

        # ========== 回滚选项 ==========
        ArgumentParser._add_rollback_arguments(parser)

        # ========== macOS 开发选项 ==========
        ArgumentParser._add_macos_arguments(parser)

        return parser.parse_args()

    @staticmethod
    def _add_basic_arguments(parser: argparse.ArgumentParser):
        """添加基本参数"""
        parser.add_argument("project_dir", help="Python项目根目录路径")
        parser.add_argument("--config", help="配置文件路径 (JSON格式)", default=None)
        parser.add_argument("--name", help="应用程序名称", default=None)
        parser.add_argument("--display-name", help="应用程序显示名称", default=None)
        parser.add_argument("--entry", help="入口Python文件", default="main.py")
        parser.add_argument("--version", help="应用程序版本", default="1.0.0")
        parser.add_argument("--publisher", help="发布者名称", default=None)

    @staticmethod
    def _add_resource_arguments(parser: argparse.ArgumentParser):
        """添加文件和资源参数"""
        parser.add_argument("--icon", help="图标文件路径", default=None)
        parser.add_argument("--license", help="许可证文件路径", default=None)
        parser.add_argument("--readme", help="自述文件路径", default=None)
        parser.add_argument("--hooks", help="运行时钩子目录", default=None)

    @staticmethod
    def _add_pyinstaller_arguments(parser: argparse.ArgumentParser):
        """添加 PyInstaller 选项"""
        parser.add_argument(
            "--onefile",
            help="生成单文件模式的可执行文件",
            action="store_true"
        )
        parser.add_argument(
            "--windowed",
            help="窗口模式（不显示控制台）",
            action="store_true"
        )
        parser.add_argument(
            "--console",
            help="控制台模式",
            action="store_true"
        )

    @staticmethod
    def _add_build_arguments(parser: argparse.ArgumentParser):
        """添加构建选项"""
        parser.add_argument(
            "--skip-exe",
            help="跳过可执行文件构建",
            action="store_true"
        )
        parser.add_argument(
            "--skip-installer",
            help="跳过安装程序构建",
            action="store_true"
        )
        parser.add_argument(
            "--dry-run",
            help="只运行环境检查与准备阶段，跳过构建与打包",
            action="store_true"
        )
        parser.add_argument(
            "--clean",
            help="清理之前的构建文件",
            action="store_true"
        )
        parser.add_argument(
            "--inno-setup-path",
            help="Inno Setup可执行文件路径",
            default=None
        )

    @staticmethod
    def _add_output_arguments(parser: argparse.ArgumentParser):
        """添加输出控制参数"""
        parser.add_argument(
            "--verbose",
            "-v",
            help="显示详细输出",
            action="store_true"
        )
        parser.add_argument(
            "--quiet",
            "-q",
            help="静默模式",
            action="store_true"
        )

    @staticmethod
    def _add_platform_arguments(parser: argparse.ArgumentParser):
        """添加平台选项"""
        parser.add_argument(
            "--format",
            help="输出格式 (exe,dmg,deb,rpm)",
            default=None
        )

    @staticmethod
    def _add_performance_arguments(parser: argparse.ArgumentParser):
        """添加性能选项"""
        parser.add_argument(
            "--parallel",
            help="启用并行构建",
            action="store_true"
        )
        parser.add_argument(
            "--max-workers",
            help="最大并行工作线程数",
            type=int,
            default=None
        )

    @staticmethod
    def _add_rollback_arguments(parser: argparse.ArgumentParser):
        """添加回滚选项"""
        parser.add_argument(
            "--no-rollback",
            help="禁用自动回滚",
            action="store_true"
        )
        parser.add_argument(
            "--rollback-keep",
            help="保留最近的回滚会话数量（0 表示不清理）",
            type=int,
            default=3
        )
        parser.add_argument(
            "--rollback",
            help="执行指定会话的回滚",
            metavar="SESSION_ID"
        )
        parser.add_argument(
            "--list-rollback",
            help="列出可用的回滚会话",
            action="store_true"
        )

    @staticmethod
    def _add_macos_arguments(parser: argparse.ArgumentParser):
        """添加 macOS 开发选项"""
        parser.add_argument(
            "--development",
            help="强制开发版本（启用调试权限）",
            action="store_true"
        )
        parser.add_argument(
            "--production",
            help="生产版本（禁用调试权限，仅用于签名应用）",
            action="store_true"
        )
