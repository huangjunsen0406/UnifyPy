#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
命令行参数解析器
负责解析和验证命令行参数
"""

import argparse
from typing import Any

from unifypy.core.version import get_version


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
  unifypy . --config build.json
  unifypy /path/to/project --name myapp --app-version 1.0.0
  unifypy . --config build.json --verbose
  unifypy . --config build.json --allow-auto-install
  unifypy --version
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

        # ========== 工具自动安装 ==========
        ArgumentParser._add_tool_arguments(parser)

        return parser.parse_args()

    @staticmethod
    def _add_basic_arguments(parser: argparse.ArgumentParser):
        """添加基本参数"""
        # 可选位置参数，便于 `unifypy --version` 无需 project_dir
        parser.add_argument(
            "project_dir",
            nargs="?",
            default=".",
            help="Python项目根目录路径（默认当前目录）",
        )
        parser.add_argument("--config", help="配置文件路径 (JSON格式)", default=None)
        parser.add_argument(
            "--init",
            help="启动交互式配置向导，生成 build.json",
            action="store_true"
        )
        parser.add_argument("--name", help="应用程序名称", default=None)
        parser.add_argument("--display-name", help="应用程序显示名称", default=None)
        parser.add_argument("--entry", help="入口Python文件", default=None)
        # 应用版本（构建产物）；工具版本用 --version
        parser.add_argument(
            "--app-version",
            help="应用程序版本",
            default=None,
            dest="version",
        )
        parser.add_argument(
            "--version",
            action="version",
            version=f"unifypy {get_version()}",
            help="显示 UnifyPy 工具版本并退出",
        )
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
            action="store_true",
            default=None,
        )
        parser.add_argument(
            "--windowed",
            help="窗口模式（不显示控制台）",
            action="store_true",
            default=None,
        )
        parser.add_argument(
            "--console",
            help="控制台模式",
            action="store_true",
            default=None,
        )

    @staticmethod
    def _add_build_arguments(parser: argparse.ArgumentParser):
        """添加构建选项"""
        parser.add_argument(
            "--skip-exe",
            help="跳过可执行文件构建",
            action="store_true",
            default=None,
        )
        parser.add_argument(
            "--skip-installer",
            help="跳过安装程序构建",
            action="store_true",
            default=None,
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
        output_group = parser.add_mutually_exclusive_group()
        output_group.add_argument(
            "--verbose",
            "-v",
            help="显示详细输出",
            action="store_true"
        )
        output_group.add_argument(
            "--quiet",
            "-q",
            help="静默模式（降低进度输出）",
            action="store_true"
        )

    @staticmethod
    def _add_platform_arguments(parser: argparse.ArgumentParser):
        """添加平台选项"""
        parser.add_argument(
            "--format",
            help="输出格式 (exe,dmg,deb,rpm,appimage)",
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
            help="启用开发版 entitlements（调试相关权限；默认 production）",
            action="store_true"
        )
        parser.add_argument(
            "--production",
            help="生产版本（默认行为，禁用调试权限）",
            action="store_true"
        )

    @staticmethod
    def _add_tool_arguments(parser: argparse.ArgumentParser):
        """添加工具安装相关参数"""
        parser.add_argument(
            "--allow-auto-install",
            help="允许自动安装缺失工具（sudo 装包、下载 appimagetool 等；Inno Setup 仍需手动安装）",
            action="store_true",
            default=False,
        )
