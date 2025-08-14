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

        # 查找.app bundle
        app_path = self._find_app_bundle(source_path)

        # 如果没有找到.app bundle，且源路径是单个可执行文件，需要创建.app结构
        if not app_path and source_path.is_file():
            app_path = self._create_app_bundle(source_path, dmg_config)
            if not app_path:
                return False
        elif not app_path:
            self.progress.on_error(
                Exception(
                    f"无法找到 .app bundle，DMG 打包需要 .app 文件：{source_path}"
                ),
                "macOS DMG打包",
            )
            return False

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

    def _find_app_bundle(self, source_path: Path) -> Path:
        """查找.app bundle.

        Args:
            source_path: 源路径（可能是目录或文件）

        Returns:
            Path: .app bundle路径，如果未找到返回None
        """
        if source_path.is_file():
            # 如果是文件，检查是否是.app bundle内的可执行文件
            return None

        # 如果是目录，查找.app bundle
        if source_path.is_dir():
            # 首先检查源路径本身是否是.app bundle
            if source_path.name.endswith(".app"):
                return source_path

            # 在目录中查找.app bundle
            for item in source_path.iterdir():
                if item.is_dir() and item.name.endswith(".app"):
                    return item

            # 如果源路径是PyInstaller输出目录，检查父目录中是否有同名的.app文件
            parent = source_path.parent
            if parent.exists():
                app_name = source_path.name + ".app"
                app_path = parent / app_name
                if app_path.exists() and app_path.is_dir():
                    return app_path

        return None

    def _create_app_bundle(self, exe_path: Path, config: Dict[str, Any]) -> Path:
        """为单个可执行文件创建.app包结构.

        Args:
            exe_path: 可执行文件路径
            config: DMG配置

        Returns:
            Path: 生成的.app路径，失败返回None
        """
        app_name = self.config.get("name", "MyApp")
        app_dir = exe_path.parent / f"{app_name}.app"

        try:
            # 创建.app目录结构
            contents_dir = app_dir / "Contents"
            macos_dir = contents_dir / "MacOS"
            resources_dir = contents_dir / "Resources"

            contents_dir.mkdir(parents=True, exist_ok=True)
            macos_dir.mkdir(exist_ok=True)
            resources_dir.mkdir(exist_ok=True)

            # 复制可执行文件
            app_exe = macos_dir / app_name
            shutil.copy2(exe_path, app_exe)
            app_exe.chmod(0o755)  # 确保可执行

            # 创建Info.plist
            info_plist = self._create_info_plist(config)
            with open(contents_dir / "Info.plist", "w") as f:
                f.write(info_plist)

            # 复制图标文件（如果有）
            icon_path = config.get("icon") or self.config.get("icon")
            if icon_path and os.path.exists(icon_path):
                icon_ext = Path(icon_path).suffix.lower()
                if icon_ext == ".icns":
                    shutil.copy2(icon_path, resources_dir / "app.icns")
                elif icon_ext in [".png", ".jpg", ".jpeg"]:
                    # 转换为icns格式（如果可能）
                    self._convert_icon_to_icns(icon_path, resources_dir / "app.icns")

            return app_dir

        except Exception as e:
            self.progress.on_error(Exception(f"创建.app包失败: {e}"), "macOS DMG打包")
            return None

    def _create_info_plist(self, config: Dict[str, Any]) -> str:
        """
        创建Info.plist文件内容.
        """
        app_name = self.config.get("name", "MyApp")
        app_version = self.config.get("version", "1.0.0")
        bundle_id = config.get("bundle_identifier", f"com.example.{app_name.lower()}")

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>{app_name}</string>
    <key>CFBundleExecutable</key>
    <string>{app_name}</string>
    <key>CFBundleIconFile</key>
    <string>app.icns</string>
    <key>CFBundleIdentifier</key>
    <string>{bundle_id}</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>{app_name}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>{app_version}</string>
    <key>CFBundleVersion</key>
    <string>{app_version}</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.9</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>"""

    def _convert_icon_to_icns(self, icon_path: str, output_path: Path):
        """
        将图标转换为icns格式.
        """
        try:
            # 使用macOS的iconutil工具
            import tempfile

            with tempfile.TemporaryDirectory() as temp_dir:
                iconset_dir = Path(temp_dir) / "icon.iconset"
                iconset_dir.mkdir()

                # 生成不同尺寸的图标
                sizes = [16, 32, 64, 128, 256, 512, 1024]

                for size in sizes:
                    # 使用sips调整图标大小
                    resized_icon = iconset_dir / f"icon_{size}x{size}.png"
                    cmd = [
                        "sips",
                        "-z",
                        str(size),
                        str(size),
                        icon_path,
                        "--out",
                        str(resized_icon),
                    ]
                    self.runner.run_command(
                        cmd, "图标转换", f"生成{size}x{size}图标", 5, shell=False
                    )

                # 转换为icns
                cmd = [
                    "iconutil",
                    "-c",
                    "icns",
                    str(iconset_dir),
                    "-o",
                    str(output_path),
                ]
                self.runner.run_command(
                    cmd, "图标转换", "生成icns文件", 10, shell=False
                )

        except Exception as e:
            self.progress.warning(f"图标转换失败: {e}")

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
        if not config.get("auto_open", False):
            command.append("--sandbox-safe")

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
