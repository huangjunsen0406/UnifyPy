#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MacOS DMG 打包器 使用create-dmg工具创建DMG安装包.
"""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

from ..base import BasePackager


class DMGPackager(BasePackager):
    """
    DMG 打包器.
    """

    def get_supported_formats(self) -> List[str]:
        """
        获取支持的打包格式.
        """
        return ["dmg"]

    def can_package_format(self, format_type: str) -> bool:
        """
        检查是否支持指定格式.
        """
        return format_type in self.get_supported_formats()

    def package(self, format_type: str, source_path: Path, output_path: Path) -> bool:
        """执行DMG打包.

        Args:
            format_type: 打包格式 (dmg)
            source_path: PyInstaller生成的.app目录路径
            output_path: 输出DMG文件路径

        Returns:
            bool: 打包是否成功
        """
        if not self.can_package_format(format_type):
            self.progress.on_error(
                Exception(f"不支持的格式: {format_type}"), "macOS DMG打包"
            )
            return False

        # 确保create-dmg工具可用
        create_dmg_path = self.tool_manager.ensure_tool("create-dmg")
        if not create_dmg_path:
            self.progress.on_error(Exception("无法获取create-dmg工具"), "macOS DMG打包")
            return False

        # 获取DMG配置
        dmg_config = self.get_format_config("dmg")

        # 验证 source_path 是 .app bundle
        if not source_path.exists():
            self.progress.on_error(
                Exception(f".app bundle 不存在: {source_path}"),
                "macOS DMG打包"
            )
            return False

        if not source_path.is_dir() or not source_path.name.endswith(".app"):
            self.progress.on_error(
                Exception(f"source_path 不是有效的 .app bundle: {source_path}"),
                "macOS DMG打包"
            )
            return False

        app_path = source_path

        # 构建create-dmg命令
        command = self._build_create_dmg_command(
            dmg_config, app_path, output_path, create_dmg_path
        )

        # 执行命令
        success = self.runner.run_command(
            command, "macOS DMG打包", "正在创建DMG安装包...", 80, shell=False
        )

        if success and output_path.exists():
            return True
        else:
            self.progress.on_error(
                Exception(f"DMG文件生成失败: {output_path}"), "macOS DMG打包"
            )
            return False

    def _build_create_dmg_command(
        self,
        config: Dict[str, Any],
        app_path: Path,
        output_path: Path,
        create_dmg_path: str,
    ) -> List[str]:
        """
        构建create-dmg命令.
        """
        command = [create_dmg_path]

        # 基本选项
        volname = config.get("volname", f"{self.config.get('name', 'MyApp')} Installer")
        command.extend(["--volname", volname])

        # 窗口设置
        if "window_size" in config:
            window_size = config["window_size"]
            if isinstance(window_size, list) and len(window_size) == 2:
                command.extend(
                    ["--window-size", str(window_size[0]), str(window_size[1])]
                )

        if "window_pos" in config:
            window_pos = config["window_pos"]
            if isinstance(window_pos, list) and len(window_pos) == 2:
                command.extend(["--window-pos", str(window_pos[0]), str(window_pos[1])])

        # 图标设置
        if "icon_size" in config:
            command.extend(["--icon-size", str(config["icon_size"])])

        # 背景图片
        background = config.get("background")
        if background and os.path.exists(background):
            command.extend(["--background", background])

        # 卷图标
        volicon = config.get("volicon")
        if volicon and os.path.exists(volicon):
            command.extend(["--volicon", volicon])

        # 应用程序文件夹链接
        if config.get("app_drop_link", True):
            app_drop_x = config.get("app_drop_x", 448)
            app_drop_y = config.get("app_drop_y", 120)
            command.extend(["--app-drop-link", str(app_drop_x), str(app_drop_y)])

        # 图标位置
        if "icon_position" in config:
            icon_pos = config["icon_position"]
            if isinstance(icon_pos, list) and len(icon_pos) == 2:
                command.extend(
                    ["--icon", app_path.name, str(icon_pos[0]), str(icon_pos[1])]
                )

        # 格式选项
        dmg_format = config.get("format", "UDZO")  # UDZO是默认压缩格式
        command.extend(["--format", dmg_format])

        # 文件系统
        filesystem = config.get("filesystem")
        if filesystem:
            command.extend(["--filesystem", filesystem])

        # 隐藏扩展名
        if config.get("hide_extension", False):
            command.append("--hide-extension")

        # 许可协议
        eula = config.get("eula")
        if eula and os.path.exists(eula):
            command.extend(["--eula", eula])

        # 详细输出
        if config.get("verbose", False):
            command.append("--hdiutil-verbose")

        # 自动打开设置（默认禁用自动打开以避免干扰）
        # 注意：--sandbox-safe 参数可能导致DMG创建问题，暂时移除
        # if not config.get("auto_open", False):
        #     command.append("--sandbox-safe")

        # 输出文件和源文件
        command.extend([str(output_path), str(app_path)])

        return command

    def validate_config(self, format_type: str) -> List[str]:
        """验证DMG配置.

        配置选项说明：
        - auto_open (bool): 是否在创建后自动打开DMG，默认为False（禁用）
        - volname (str): DMG卷名称
        - window_size (list): 窗口大小 [width, height]
        - window_pos (list): 窗口位置 [x, y]
        - icon_size (int): 图标大小
        - background (str): 背景图片路径
        - volicon (str): 卷图标路径
        - app_drop_link (bool): 是否添加应用程序文件夹链接
        - format (str): DMG格式 (UDZO|UDBZ|ULFO|ULMO)
        - filesystem (str): 文件系统 (HFS+|APFS)
        - eula (str): 许可协议文件路径
        """
        errors = []

        config = self.get_format_config("dmg")

        # 检查背景图片
        background = config.get("background")
        if background and not os.path.exists(background):
            errors.append(f"背景图片文件不存在: {background}")

        # 检查卷图标
        volicon = config.get("volicon")
        if volicon and not os.path.exists(volicon):
            errors.append(f"卷图标文件不存在: {volicon}")

        # 检查许可协议文件
        eula = config.get("eula")
        if eula and not os.path.exists(eula):
            errors.append(f"许可协议文件不存在: {eula}")

        return errors
