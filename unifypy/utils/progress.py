#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
进度条管理系统 提供统一的进度显示和状态管理.
"""

import time
from typing import Any, Dict

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    TaskID,
    TextColumn,
)
from rich.table import Table
from rich.text import Text


class CustomTimeColumn(ProgressColumn):
    """
    自定义时间列，显示阶段用时.
    """

    def __init__(self, progress_manager):
        super().__init__()
        self.progress_manager = progress_manager

    def render(self, task):
        """
        渲染时间显示.
        """
        # 查找对应的阶段名称
        stage_name = None
        for name, task_id in self.progress_manager.tasks.items():
            if task_id == task.id:
                stage_name = name
                break

        if stage_name and stage_name in self.progress_manager.stage_start_times:
            # 如果任务已完成（包括进度超过100%的情况），显示最终用时
            if task.completed >= task.total or task.percentage >= 100:
                if stage_name in self.progress_manager.stage_durations:
                    duration = self.progress_manager.stage_durations[stage_name]
                    return Text(
                        self.progress_manager._format_duration(duration), style="green"
                    )
                else:
                    # 如果还没有记录最终用时，计算当前用时
                    current_time = time.time()
                    elapsed = (
                        current_time
                        - self.progress_manager.stage_start_times[stage_name]
                    )
                    return Text(
                        self.progress_manager._format_duration(elapsed), style="green"
                    )
            else:
                # 如果任务进行中，显示实时用时
                current_time = time.time()
                elapsed = (
                    current_time - self.progress_manager.stage_start_times[stage_name]
                )
                return Text(
                    self.progress_manager._format_duration(elapsed), style="yellow"
                )

        return Text("0:00:00", style="dim")


class ProgressManager:
    """
    统一的进度管理器.
    """

    def __init__(self, verbose: bool = False, quiet: bool = False):
        """初始化进度管理器.

        Args:
            verbose: 是否显示详细输出
            quiet: 静默模式（降低进度输出；错误/警告仍显示）
        """
        # Do not set Console(quiet=True): that would suppress error panels too.
        self.console = Console()
        self.verbose = verbose and not quiet
        self.quiet = quiet
        self.current_stage = ""
        self.started = False

        # 创建进度条组件
        self.custom_time_column = CustomTimeColumn(self)
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            MofNCompleteColumn(),
            self.custom_time_column,
            console=self.console,
            expand=True,
            refresh_per_second=10,  # 每秒刷新10次，确保时间显示实时更新
        )

        self.tasks: Dict[str, TaskID] = {}
        self.stage_start_times: Dict[str, float] = {}
        self.stage_durations: Dict[str, float] = {}
        self.stage_weights = {
            "环境检查": 10,
            "PyInstaller打包": 40,
            "安装包生成": 40,
            "验证和清理": 10,
        }

    def start(self):
        """
        启动进度显示.
        """
        if self.quiet:
            self.started = False
            return
        if not self.verbose:
            self.progress.start()
            self._show_header()
        self.started = True

    def stop(self):
        """
        停止进度显示.
        """
        if self.quiet:
            return
        if not self.verbose:
            self.progress.stop()

    def _show_header(self):
        """
        显示程序头部信息.
        """
        header = Panel(
            Text("🚀 UnifyPy 2.0 - 跨平台Python应用打包工具", style="bold blue"),
            subtitle="正在打包您的应用程序...",
            border_style="blue",
        )
        self.console.print(header)
        self.console.print()

    def start_stage(
        self, stage_name: str, description: str = "", total: int = 100
    ) -> TaskID:
        """开始新的阶段.

        Args:
            stage_name: 阶段名称
            description: 阶段描述
            total: 总进度值

        Returns:
            TaskID: 任务ID
        """
        self.current_stage = stage_name
        self.stage_start_times[stage_name] = time.time()

        if self.quiet:
            return None

        if self.verbose:
            self.console.print(f"\n🔄 开始阶段: {stage_name}")
            if description:
                self.console.print(f"   {description}")
            return None

        display_name = f"{stage_name}: {description}" if description else stage_name
        task_id = self.progress.add_task(display_name, total=total)
        self.tasks[stage_name] = task_id

        return task_id

    def update_stage(
        self,
        stage_name: str,
        advance: int = 1,
        description: str = None,
        absolute: bool = False,
    ):
        """更新阶段进度.

        Args:
            stage_name: 阶段名称
            advance: 进度增量或绝对进度值
            description: 更新描述
            absolute: 如果为True，advance表示绝对进度值；如果为False，表示增量
        """
        if self.quiet:
            return

        if self.verbose and description:
            self.console.print(f"   • {description}")
            return

        if stage_name in self.tasks:
            task_id = self.tasks[stage_name]
            if absolute:
                # 绝对进度设置
                if description:
                    self.progress.update(
                        task_id,
                        completed=advance,
                        description=f"{stage_name}: {description}",
                    )
                else:
                    self.progress.update(task_id, completed=advance)
            else:
                # 增量进度更新
                if description:
                    self.progress.update(
                        task_id,
                        advance=advance,
                        description=f"{stage_name}: {description}",
                    )
                else:
                    self.progress.update(task_id, advance=advance)

    def complete_stage(self, stage_name: str):
        """完成阶段.

        Args:
            stage_name: 阶段名称
        """
        # 计算阶段耗时
        if stage_name in self.stage_start_times:
            duration = time.time() - self.stage_start_times[stage_name]
            self.stage_durations[stage_name] = duration
            duration_str = self._format_duration(duration)

            if self.quiet:
                return

            if self.verbose:
                self.console.print(f"✅ 完成阶段: {stage_name} (用时: {duration_str})")
                return

            # 标记任务完成，时间显示由自定义时间列处理
            if stage_name in self.tasks:
                task_id = self.tasks[stage_name]
                self.progress.update(task_id, completed=100)
        else:
            if self.quiet:
                return
            if self.verbose:
                self.console.print(f"✅ 完成阶段: {stage_name}")
                return

            if stage_name in self.tasks:
                task_id = self.tasks[stage_name]
                self.progress.update(task_id, completed=100)

    def on_error(self, error: Exception, stage: str, details: str = ""):
        """错误处理.

        Args:
            error: 异常对象
            stage: 发生错误的阶段
            details: 错误详情
        """
        # Stop progress bar only if it was started (quiet mode never starts it)
        if not self.verbose and not self.quiet and self.started:
            self.progress.stop()

        # 显示错误信息（quiet 模式仍输出错误）
        error_panel = Panel(
            f"[red]❌ 错误发生在 {stage}[/red]\n\n"
            f"[yellow]错误信息:[/yellow] {str(error)}\n"
            f"{details if details else ''}",
            title="[red]打包失败[/red]",
            border_style="red",
        )
        self.console.print(error_panel)

        # 提供解决建议（传入 details，便于识别 non-empty dist 等线索）
        self._show_error_suggestions(error, stage, details=details)

    @staticmethod
    def build_error_suggestions(
        error: Exception, stage: str, details: str = ""
    ) -> list:
        """Build user-facing recovery hints for a failed stage.

        Non-empty dist / COLLECT failures must suggest ``--clean``, not a
        misleading PyInstaller upgrade.
        """
        suggestions = []
        error_str = str(error).lower()
        details_str = (details or "").lower()
        combined = f"{error_str}\n{details_str}"

        if "permission" in error_str or "access" in error_str:
            suggestions.append("• 尝试以管理员权限运行")
            suggestions.append("• 检查文件/目录权限设置")

        if "not found" in error_str or "command not found" in error_str:
            suggestions.append("• 检查相关工具是否已安装")
            suggestions.append("• 确认PATH环境变量设置正确")

        # Non-empty dist / COLLECT dir: prefer --clean, not "upgrade PyInstaller"
        non_empty_dist = (
            "is not empty" in combined
            or "not empty" in combined
            or "remove the output directory" in combined
            or "输出目录非空" in combined
            or "非空" in error_str
        )
        if non_empty_dist or "--clean" in error_str:
            suggestions.append(
                "• 使用 `unifypy <project_dir> --clean` 清理输出目录后重试"
            )
            suggestions.append(
                "• UnifyPy 默认对 pyinstaller 传入 `-y`；若仍失败请确认未绕过 UnifyPy 直接调用"
            )
        elif "pyinstaller" in error_str or "pyinstaller" in stage.lower():
            suggestions.append(
                "• 尝试升级PyInstaller: pip install --upgrade pyinstaller"
            )
            suggestions.append("• 检查Python依赖是否完整")

        if stage == "环境检查":
            suggestions.append("• 确认配置文件格式正确")
            suggestions.append("• 检查项目目录结构")

        return suggestions

    def _show_error_suggestions(self, error: Exception, stage: str, details: str = ""):
        """显示错误解决建议."""
        suggestions = self.build_error_suggestions(error, stage, details=details)
        if suggestions:
            suggestion_text = "\n".join(suggestions)
            suggestion_panel = Panel(
                suggestion_text,
                title="[yellow]💡 解决建议[/yellow]",
                border_style="yellow",
            )
            self.console.print(suggestion_panel)

    def show_success(self, output_info: Dict[str, Any]):
        """显示成功信息.

        Args:
            output_info: 输出信息字典
        """
        if not self.verbose and not self.quiet and self.started:
            self.progress.stop()

        # quiet: 仅简要列出产物路径
        if self.quiet:
            for item_type, file_path in output_info.items():
                if isinstance(file_path, str) and file_path:
                    self.console.print(f"{item_type}: {file_path}")
            return

        # 创建结果表格
        table = Table(
            title="🎉 打包成功完成！", show_header=True, header_style="bold green"
        )
        table.add_column("类型", style="cyan")
        table.add_column("文件路径", style="green")
        table.add_column("大小", style="yellow")

        for item_type, file_path in output_info.items():
            if isinstance(file_path, str) and file_path:
                try:
                    size = self._format_size(self._path_size(file_path))
                    table.add_row(item_type, file_path, size)
                except Exception:
                    table.add_row(item_type, file_path, "未知")

        self.console.print(table)
        self.console.print(
            "\n[green]✨ 打包完成！您可以分发这些文件给用户使用。[/green]"
        )

    def _path_size(self, file_path: str) -> int:
        """Total size of a file, or recursive size of a directory (.app, onedir)."""
        import os
        from pathlib import Path

        path = Path(file_path)
        if path.is_file():
            return path.stat().st_size
        if path.is_dir():
            total = 0
            for root, _dirs, files in os.walk(path):
                for name in files:
                    try:
                        total += os.path.getsize(os.path.join(root, name))
                    except OSError:
                        continue
            return total
        return path.stat().st_size

    def _format_size(self, size: int) -> str:
        """
        格式化文件大小.
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _format_duration(self, duration: float) -> str:
        """
        格式化持续时间.
        """
        if duration < 1:
            return f"{duration*1000:.0f}ms"
        elif duration < 60:
            return f"{duration:.1f}s"
        else:
            minutes = int(duration // 60)
            seconds = duration % 60
            return f"{minutes}m{seconds:.1f}s"

    def info(self, message: str):
        """
        显示信息（quiet 下不输出进度类 info；verbose 才打印）.
        """
        if self.quiet:
            return
        if self.verbose:
            self.console.print(f"ℹ️  {message}")

    def warning(self, message: str):
        """
        显示警告（quiet 仍输出）.
        """
        self.console.print(f"[yellow]⚠️  {message}[/yellow]")

    def success(self, message: str):
        """
        显示成功信息.
        """
        if self.quiet:
            return
        self.console.print(f"[green]✅ {message}[/green]")
