#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
静默命令执行器 只在错误时输出详细信息.
"""

import subprocess
import sys
import locale
from typing import List, Optional, Union

from .progress import ProgressManager


def get_subprocess_encoding() -> str:
    """
    获取 subprocess 输出的适当编码

    根据系统区域设置自动选择编码：
    - Windows: 通常是 cp936(GBK), cp950(Big5), cp932(Shift-JIS) 等
    - macOS/Linux: 通常是 UTF-8

    Returns:
        str: 编码名称
    """
    try:
        # getpreferredencoding(False) 返回系统默认编码
        # False 参数表示不使用 locale.CODESET（更可靠）
        encoding = locale.getpreferredencoding(False)
        if encoding and encoding.lower() not in (
            'ascii', 'ansi_x3.4-1968'
        ):
            return encoding
    except Exception:
        pass

    # 回退到 UTF-8
    return 'utf-8'


class SilentRunner:
    """
    静默命令执行器，只在错误时输出.
    """

    def __init__(self, progress_manager: ProgressManager):
        """初始化命令执行器.

        Args:
            progress_manager: 进度管理器实例
        """
        self.progress = progress_manager
        self.log_buffer = []

    def run_command(
        self,
        command: Union[str, List[str]],
        stage: str,
        step_description: str = "",
        step_weight: int = 10,
        capture_output: bool = True,
        shell: bool = True,
        cwd: Optional[str] = None,
    ) -> bool:
        """执行命令，只在错误时显示输出.

        Args:
            command: 要执行的命令
            stage: 当前阶段名称
            step_description: 步骤描述
            step_weight: 进度权重
            capture_output: 是否捕获输出
            shell: 是否使用shell执行

        Returns:
            bool: 执行是否成功
        """
        # 更新进度描述
        if step_description:
            self.progress.update_stage(stage, advance=0, description=step_description)

        # 在verbose模式下显示执行的命令
        if self.progress.verbose:
            cmd_str = " ".join(command) if isinstance(command, list) else command
            self.progress.info(f"执行命令: {cmd_str}")

        try:
            # 获取系统适当的编码
            encoding = get_subprocess_encoding()

            # 执行命令
            if capture_output:
                result = subprocess.run(
                    command,
                    shell=shell,
                    capture_output=True,
                    text=True,
                    encoding=encoding,
                    # 无法解码的字节替换为 � (防止崩溃)
                    errors='replace',
                    cwd=cwd,
                )
            else:
                result = subprocess.run(
                    command,
                    shell=shell,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding=encoding,
                    # 无法解码的字节替换为 � (防止崩溃)
                    errors='replace',
                    cwd=cwd,
                )

            # 检查执行结果
            if result.returncode == 0:
                # 成功时更新进度
                self.progress.update_stage(stage, advance=step_weight)

                # 在verbose模式下显示输出
                if (
                    self.progress.verbose
                    and hasattr(result, "stdout")
                    and result.stdout
                ):
                    self.progress.info(f"输出: {result.stdout.strip()}")

                return True
            else:
                # 失败时显示错误信息
                error_msg = f"命令执行失败 (返回码: {result.returncode})"

                details = ""
                if hasattr(result, "stderr") and result.stderr:
                    details += f"\n[red]错误输出:[/red]\n{result.stderr}"
                if hasattr(result, "stdout") and result.stdout:
                    details += f"\n[yellow]标准输出:[/yellow]\n{result.stdout}"

                cmd_str = " ".join(command) if isinstance(command, list) else command
                details += f"\n[cyan]执行的命令:[/cyan]\n{cmd_str}"

                self.progress.on_error(Exception(error_msg), stage, details)
                return False

        except FileNotFoundError as e:
            self.progress.on_error(
                Exception(f"命令未找到: {e}"),
                stage,
                f"\n请确认相关工具已正确安装并在PATH中。\n命令: {command}",
            )
            return False

        except KeyboardInterrupt:
            # 传递给上层，由引擎统一处理
            raise
        except Exception as e:
            self.progress.on_error(e, stage)
            return False

    def run_python_script(
        self,
        script_path: str,
        args: List[str],
        stage: str,
        step_description: str = "",
        step_weight: int = 10,
    ) -> bool:
        """执行Python脚本.

        Args:
            script_path: 脚本路径
            args: 脚本参数
            stage: 当前阶段
            step_description: 步骤描述
            step_weight: 进度权重

        Returns:
            bool: 执行是否成功
        """
        command = [sys.executable, script_path] + args
        return self.run_command(
            command, stage, step_description, step_weight, shell=False
        )

    def check_tool_available(self, tool_name: str) -> bool:
        """检查工具是否可用.

        Args:
            tool_name: 工具名称

        Returns:
            bool: 工具是否可用
        """
        try:
            result = subprocess.run(
                [tool_name, "--version"],
                capture_output=True,
                text=True,
                encoding=get_subprocess_encoding(),
                errors='replace',
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            # 有些工具可能不支持--version，尝试--help
            try:
                result = subprocess.run(
                    [tool_name, "--help"],
                    capture_output=True,
                    text=True,
                    encoding=get_subprocess_encoding(),
                    errors='replace',
                )
                return result.returncode == 0
            except Exception:
                return False

    def get_tool_version(self, tool_name: str) -> Optional[str]:
        """获取工具版本.

        Args:
            tool_name: 工具名称

        Returns:
            Optional[str]: 工具版本，如果无法获取则返回None
        """
        try:
            result = subprocess.run(
                [tool_name, "--version"],
                capture_output=True,
                text=True,
                encoding=get_subprocess_encoding(),
                errors='replace',
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
