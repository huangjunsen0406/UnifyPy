#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包器注册表 支持动态添加新的打包格式.
"""

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

    def _load_default_packagers(self):
        """
        加载默认打包器.
        """
        try:
            # Windows 打包器
            from .windows.inno_setup import InnoSetupPackager
            from .windows.msi_packager import MSIPackager

            self.register_packager("windows", "exe", InnoSetupPackager)
            self.register_packager("windows", "msi", MSIPackager)

            # macOS 打包器
            from .macos.dmg_packager import DMGPackager

            self.register_packager("macos", "dmg", DMGPackager)

            # Linux 打包器
            from .linux.appimage_packager import AppImagePackager
            from .linux.deb_packager import DEBPackager
            from .linux.rpm_packager import RPMPackager
            from .linux.tarball_packager import TarballPackager

            self.register_packager("linux", "deb", DEBPackager)
            self.register_packager("linux", "rpm", RPMPackager)
            self.register_packager("linux", "appimage", AppImagePackager)
            self.register_packager("linux", "tar.gz", TarballPackager)

        except ImportError:
            # 如果某些平台的打包器模块不存在，忽略错误
            pass

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
