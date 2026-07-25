#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
并行构建器 支持多个构建步骤的并行处理.
"""

import concurrent.futures
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class ParallelBuilder:
    """
    并行构建器，支持多格式同时打包.
    """

    def __init__(self, progress_manager, max_workers: Optional[int] = None):
        """初始化并行构建器.

        Args:
            progress_manager: 进度管理器
            max_workers: 最大工作线程数，默认为CPU核心数
        """
        self.progress = progress_manager
        self.max_workers = max_workers or min(4, (os.cpu_count() or 1) + 1)
        self._executor = None

    def __enter__(self):
        """
        进入上下文管理器.
        """
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        退出上下文管理器.
        """
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None

    def build_multiple_formats(
        self,
        platform: str,
        formats: List[str],
        packager_registry,
        source_path: Path,
        output_dir: Path,
        config: Dict[str, Any],
        config_file_path: Optional[str] = None,
        project_dir=None,
    ) -> Dict[str, bool]:
        """并行构建多种格式的安装包.

        Args:
            platform: 平台名称
            formats: 格式列表
            packager_registry: 打包器注册表
            source_path: 源文件路径
            output_dir: 输出目录
            config: 配置字典
            config_file_path: 配置文件路径
            project_dir: 用户项目根目录

        Returns:
            Dict[str, bool]: 每种格式的构建结果
        """
        if not self._executor:
            raise RuntimeError("ParallelBuilder must be used as a context manager")

        # 准备任务
        tasks = []
        format_info = {}

        for format_type in formats:
            packager_class = packager_registry.get_packager(platform, format_type)
            if not packager_class:
                self.progress.warning(f"未找到 {platform}/{format_type} 格式的打包器")
                continue

            # 创建打包器实例
            packager = packager_class(
                self.progress,
                None,  # 每个线程将创建自己的runner
                None,  # 每个线程将创建自己的tool_manager
                config,
                config_file_path,
                project_dir=project_dir,
            )

            # 生成输出文件名
            app_name = config.get("name", "myapp")
            version = config.get("version", "1.0.0")
            output_filename = packager.get_output_filename(
                format_type, app_name, version
            )
            output_path = output_dir / output_filename

            format_info[format_type] = {
                "packager": packager,
                "source_path": source_path,
                "output_path": output_path,
                "format_type": format_type,
            }

            # 提交任务到线程池
            future = self._executor.submit(
                self._build_single_format,
                format_type,
                packager,
                source_path,
                output_path,
            )
            tasks.append((format_type, future))

        # 等待所有任务完成
        results = {}
        completed = 0
        total = len(tasks)

        for format_type, future in tasks:
            try:
                success = future.result(timeout=600)  # 10分钟超时
                results[format_type] = success
                completed += 1

                progress_percentage = int(80 * completed / total)
                status = "✅ 成功" if success else "❌ 失败"
                self.progress.update_stage(
                    "安装包生成",
                    progress_percentage,
                    f"{format_type.upper()} 格式: {status} ({completed}/{total})",
                )

            except concurrent.futures.TimeoutError:
                self.progress.on_error(
                    Exception(f"{format_type} 格式打包超时"), "并行构建"
                )
                results[format_type] = False
            except Exception as e:
                self.progress.on_error(
                    Exception(f"{format_type} 格式打包失败: {e}"), "并行构建"
                )
                results[format_type] = False

        return results

    def _build_single_format(
        self, format_type: str, packager, source_path: Path, output_path: Path
    ) -> bool:
        """构建单个格式的安装包（在独立线程中执行）

        Args:
            format_type: 格式类型
            packager: 打包器实例
            source_path: 源文件路径
            output_path: 输出文件路径

        Returns:
            bool: 构建是否成功
        """
        try:
            # 为此线程创建独立的组件
            from ..utils.command_runner import SilentRunner
            from ..utils.tool_manager import ToolManager

            runner = SilentRunner(self.progress)
            tool_manager = ToolManager()

            # 更新打包器的组件引用
            packager.runner = runner
            packager.tool_manager = tool_manager

            # 执行打包
            return packager.package(format_type, source_path, output_path)

        except Exception as e:
            self.progress.on_error(
                Exception(f"线程中构建 {format_type} 失败: {e}"), "并行构建"
            )
            return False

    def optimize_pyinstaller_build(
        self, config: Dict[str, Any], entry_script: str, project_dir: Path
    ) -> bool:
        """优化PyInstaller构建过程.

        Args:
            config: PyInstaller配置
            entry_script: 入口脚本
            project_dir: 项目目录

        Returns:
            bool: 构建是否成功
        """
        try:
            # 检查是否可以使用增量构建
            if self._can_use_incremental_build(project_dir):
                self.progress.info("使用增量构建模式...")
                config = config.copy()
                config.pop("clean", None)  # 移除clean选项

            # 检查是否可以启用PyInstaller优化
            optimizations = self._get_pyinstaller_optimizations(config)
            if optimizations:
                self.progress.info("启用PyInstaller优化选项...")
                config.update(optimizations)

            return True

        except Exception as e:
            self.progress.warning(f"PyInstaller优化失败: {e}")
            return False

    def _can_use_incremental_build(self, project_dir: Path) -> bool:
        """
        检查是否可以使用增量构建.
        """
        try:
            build_dir = project_dir / "build"
            dist_dir = project_dir / "dist"

            # 检查是否存在之前的构建
            if not (build_dir.exists() and dist_dir.exists()):
                return False

            # 检查源文件修改时间
            source_files = list(project_dir.glob("**/*.py"))
            if not source_files:
                return False

            latest_source_time = max(f.stat().st_mtime for f in source_files)

            # 检查构建目录的修改时间
            build_files = list(build_dir.glob("**/*"))
            if not build_files:
                return False

            latest_build_time = max(
                f.stat().st_mtime for f in build_files if f.is_file()
            )

            # 如果构建文件比源文件新，可以增量构建
            return latest_build_time > latest_source_time

        except Exception:
            return False

    def _get_pyinstaller_optimizations(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取PyInstaller优化选项.
        """
        optimizations = {}

        # 如果没有指定优化级别，启用基本优化
        if "optimize" not in config:
            optimizations["optimize"] = 1

        # 如果没有调试信息，启用strip
        if not config.get("debug", False) and "strip" not in config:
            optimizations["strip"] = True

        # 启用UPX压缩（如果可用且未禁用）
        if not config.get("noupx", False) and "upx_dir" not in config:
            import shutil

            if shutil.which("upx"):
                optimizations["noupx"] = False
                self.progress.info("检测到UPX，启用可执行文件压缩")

        return optimizations
