#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包器注册表 支持动态添加新的打包格式.
"""

import importlib
from typing import Dict, List, Optional, Type

from .base import BasePackager


class PackagerRegistry:
    """
    打包器注册表.
    """

    def __init__(self):
        """
        初始化注册表.
        """
        self._packagers: Dict[str, Dict[str, Type[BasePackager]]] = {}
        self._load_default_packagers()

    def _try_register(
        self, platform: str, fmt: str, import_path: str, class_name: str
    ) -> None:
        """Import and register one packager; log ImportError and continue."""
        try:
            module = importlib.import_module(import_path)
            cls = getattr(module, class_name)
            self.register_packager(platform, fmt, cls)
        except ImportError as e:
            from unifypy.core import logutil

            logutil.warn(f"Packager unavailable {platform}/{fmt}: {e}")

    def _load_default_packagers(self):
        """
        加载默认打包器（各自独立导入，单个失败不影响其余）.
        """
        defaults = [
            ("windows", "exe", "unifypy.platforms.windows.inno_setup", "InnoSetupPackager"),
            ("macos", "dmg", "unifypy.platforms.macos.dmg_packager", "DMGPackager"),
            ("linux", "appimage", "unifypy.platforms.linux.appimage_packager", "AppImagePackager"),
            ("linux", "deb", "unifypy.platforms.linux.deb_packager", "DEBPackager"),
            ("linux", "rpm", "unifypy.platforms.linux.rpm_packager", "RPMPackager"),
        ]
        for platform, fmt, import_path, class_name in defaults:
            self._try_register(platform, fmt, import_path, class_name)

    def register_packager(
        self, platform: str, format_type: str, packager_class: Type[BasePackager]
    ):
        """注册新的打包器.

        Args:
            platform: 平台名称 (windows/macos/linux)
            format_type: 格式类型 (exe/dmg/deb等)
            packager_class: 打包器类
        """
        if platform not in self._packagers:
            self._packagers[platform] = {}

        self._packagers[platform][format_type] = packager_class

    def get_packager(
        self, platform: str, format_type: str
    ) -> Optional[Type[BasePackager]]:
        """获取指定格式的打包器类.

        Args:
            platform: 平台名称
            format_type: 格式类型

        Returns:
            Optional[Type[BasePackager]]: 打包器类，如果不存在则返回None
        """
        return self._packagers.get(platform, {}).get(format_type)

    def get_supported_formats(self, platform: str) -> List[str]:
        """获取平台支持的所有格式.

        Args:
            platform: 平台名称

        Returns:
            List[str]: 支持的格式列表
        """
        return list(self._packagers.get(platform, {}).keys())

    def get_all_platforms(self) -> List[str]:
        """获取所有支持的平台.

        Returns:
            List[str]: 平台列表
        """
        return list(self._packagers.keys())

    def is_format_supported(self, platform: str, format_type: str) -> bool:
        """检查格式是否支持.

        Args:
            platform: 平台名称
            format_type: 格式类型

        Returns:
            bool: 是否支持
        """
        return format_type in self._packagers.get(platform, {})
