#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
平台打包器基类.
"""

import platform
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class BasePackager(ABC):
    """
    平台打包器基类.
    """

    def __init__(self, progress_manager, runner, tool_manager, config: Dict[str, Any]):
        """初始化打包器.

        Args:
            progress_manager: 进度管理器
            runner: 命令执行器
            tool_manager: 工具管理器
            config: 配置字典
        """
        self.progress = progress_manager
        self.runner = runner
        self.tool_manager = tool_manager
        self.config = config
        self.current_platform = self._detect_platform()

    def _detect_platform(self) -> str:
        """
        检测当前平台.
        """
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        else:
            return system

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的打包格式.

        Returns:
            List[str]: 支持的格式列表
        """

    @abstractmethod
    def can_package_format(self, format_type: str) -> bool:
        """检查是否支持指定格式.

        Args:
            format_type: 打包格式

        Returns:
            bool: 是否支持
        """

    @abstractmethod
    def package(self, format_type: str, source_path: Path, output_path: Path) -> bool:
        """执行打包.

        Args:
            format_type: 打包格式
            source_path: 源文件/目录路径
            output_path: 输出路径

        Returns:
            bool: 打包是否成功
        """

    def validate_config(self, format_type: str) -> List[str]:
        """验证配置.

        Args:
            format_type: 打包格式

        Returns:
            List[str]: 验证错误列表
        """
        return []

    def get_output_filename(self, format_type: str, app_name: str, version: str) -> str:
        """生成输出文件名.

        Args:
            format_type: 打包格式
            app_name: 应用名称
            version: 版本号

        Returns:
            str: 输出文件名
        """
        # 获取架构信息
        arch = platform.machine().lower()
        if arch == "x86_64":
            arch = "amd64"
        elif arch.startswith("arm"):
            arch = "arm64" if "64" in arch else "arm"

        return f"{app_name}-{version}-{arch}.{format_type}"

    def ensure_output_dir(self, output_path: Path) -> None:
        """确保输出目录存在.

        Args:
            output_path: 输出路径
        """
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

    def get_format_config(self, format_type: str) -> Dict[str, Any]:
        """获取格式特定的配置.

        Args:
            format_type: 打包格式

        Returns:
            Dict[str, Any]: 格式配置
        """
        platform_config = self.config.get("platforms", {}).get(
            self.current_platform, {}
        )
        return platform_config.get(format_type, {})
