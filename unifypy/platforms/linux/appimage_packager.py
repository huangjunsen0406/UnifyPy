#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Linux AppImage 打包器 创建便携式 AppImage 格式的应用包.

AppImage 是一种便携式应用格式，无需安装即可在大多数 Linux 发行版上运行。
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from ..base import BasePackager


class AppImagePackager(BasePackager):
    """
    AppImage 打包器.

    AppImage 格式特点：
    - 单文件便携式应用
    - 无需安装，直接运行
    - 包含所有依赖
    - 兼容大多数 Linux 发行版
    """

    def get_supported_formats(self) -> List[str]:
        """
        获取支持的打包格式.
        """
        return ["appimage"]

    def can_package_format(self, format_type: str) -> bool:
        """
        检查是否支持指定格式.
        """
        return format_type.lower() in self.get_supported_formats()

    def package(self, format_type: str, source_path: Path, output_path: Path) -> bool:
        """执行 AppImage 打包.

        Args:
            format_type: 打包格式 (appimage)
            source_path: PyInstaller生成的应用路径
            output_path: 输出 AppImage 文件路径

        Returns:
            bool: 打包是否成功
        """
        if not self.can_package_format(format_type):
            self.progress.on_error(
                Exception(f"不支持的格式: {format_type}"), "Linux AppImage打包"
            )
            return False

        # 获取 AppImage 配置
        appimage_config = self.get_format_config("appimage")

        # 创建临时构建目录
        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir) / "AppDir"
            app_dir.mkdir()

            # 安装应用文件到 AppDir
            self._install_application(source_path, app_dir, appimage_config)

            # 创建 AppRun 启动脚本
            self._create_apprun(app_dir, appimage_config)

            # 创建桌面文件
            self._create_desktop_file(app_dir, appimage_config)

            # 复制图标文件
            self._copy_icon(app_dir, appimage_config)

            # 构建 AppImage
            success = self._build_appimage(app_dir, output_path)

            return success

    def _install_application(
        self, source_path: Path, app_dir: Path, config: Dict[str, Any]
    ):
        """
        安装应用文件到 AppDir.

        AppDir 结构：
        AppDir/
        ├── AppRun (启动脚本)
        ├── myapp.desktop
        ├── myapp.png (图标)
        ├── myapp (主可执行文件)
        └── _internal/ (依赖文件)
        """
        app_name = self.config.get("name", "myapp")

        if source_path.is_file():
            # 单个可执行文件
            shutil.copy2(source_path, app_dir / app_name)
            (app_dir / app_name).chmod(0o755)
        else:
            # 目录 - 复制所有内容
            for item in source_path.iterdir():
                if item.is_dir():
                    shutil.copytree(item, app_dir / item.name, symlinks=True)
                else:
                    shutil.copy2(item, app_dir / item.name)
                    # 保持可执行权限
                    if os.access(item, os.X_OK):
                        (app_dir / item.name).chmod(0o755)

    def _create_apprun(self, app_dir: Path, config: Dict[str, Any]):
        """
        创建 AppRun 启动脚本.

        AppRun 是 AppImage 的入口点，负责：
        1. 确定 AppImage 挂载路径
        2. 设置环境变量
        3. 启动主应用程序
        """
        app_name = self.config.get("name", "myapp")
        apprun_path = app_dir / "AppRun"

        # 使用更兼容的路径获取方式（避免 readlink -f 的兼容性问题）
        apprun_content = f"""#!/bin/bash
# AppImage 启动脚本
# 自动生成于 UnifyPy 2.0

# 获取 AppImage 或 AppDir 的路径
SELF_DIR="$(cd "$(dirname "$0")" && pwd)"

# 切换到应用目录
cd "$SELF_DIR" || exit 1

# 启动主应用程序
exec "$SELF_DIR/{app_name}" "$@"
"""

        with open(apprun_path, "w", encoding="utf-8") as f:
            f.write(apprun_content)

        # 设置可执行权限
        apprun_path.chmod(0o755)

    def _create_desktop_file(self, app_dir: Path, config: Dict[str, Any]):
        """
        创建 .desktop 文件.

        desktop 文件定义了应用的元数据和启动方式。
        """
        app_name = self.config.get("name", "myapp")
        display_name = self.config.get("display_name", app_name)

        # 桌面文件内容
        desktop_content = f"""[Desktop Entry]
Type=Application
Name={display_name}
Exec={app_name}
Icon={app_name}
Comment={config.get('comment', self.config.get('description', display_name))}
Categories={config.get('categories', 'Utility;')}
Terminal={str(config.get('terminal', False)).lower()}
Version={self.config.get('version', '1.0.0')}
"""

        # 添加可选字段
        if config.get("generic_name"):
            desktop_content += f"GenericName={config['generic_name']}\n"

        if config.get("keywords"):
            keywords = config["keywords"]
            if isinstance(keywords, list):
                keywords = ";".join(keywords)
            desktop_content += f"Keywords={keywords};\n"

        # 写入桌面文件
        desktop_file = app_dir / f"{app_name}.desktop"
        with open(desktop_file, "w", encoding="utf-8") as f:
            f.write(desktop_content)

        # 设置可执行权限（AppImage 规范要求）
        desktop_file.chmod(0o755)

    def _copy_icon(self, app_dir: Path, config: Dict[str, Any]):
        """
        复制图标文件到 AppDir.

        AppImage 规范：
        - 图标文件名必须与应用名称相同
        - 支持 PNG, SVG 格式
        - 推荐尺寸：256x256 或更大
        """
        app_name = self.config.get("name", "myapp")
        icon_path = config.get("icon") or self.config.get("icon")

        if icon_path and os.path.exists(icon_path):
            icon_ext = Path(icon_path).suffix
            icon_dest = app_dir / f"{app_name}{icon_ext}"
            shutil.copy2(icon_path, icon_dest)
        else:
            # 如果没有图标，创建一个占位符（避免 appimagetool 警告）
            self.progress.on_warning(
                "未提供图标文件，AppImage 将使用默认图标"
            )

    def _build_appimage(self, app_dir: Path, output_path: Path) -> bool:
        """
        使用 appimagetool 构建 AppImage.

        appimagetool 是官方的 AppImage 构建工具。
        """
        # 确保输出目录存在
        self.ensure_output_dir(output_path)

        # 构建命令
        command = ["appimagetool", str(app_dir), str(output_path)]

        # 设置环境变量（避免某些系统上的权限问题）
        env = os.environ.copy()
        env["ARCH"] = self.env_manager.get_arch_for_format("appimage")

        success = self.runner.run_command(
            command,
            "Linux AppImage打包",
            "正在构建 AppImage...",
            80,
            shell=False,
            env=env,
        )

        if success and output_path.exists():
            # 设置可执行权限
            output_path.chmod(0o755)
            return True
        else:
            self.progress.on_error(
                Exception(f"AppImage 生成失败: {output_path}"),
                "Linux AppImage打包",
            )
            return False

    def validate_config(self, format_type: str) -> List[str]:
        """
        验证 AppImage 配置.

        检查项：
        1. appimagetool 工具是否安装
        2. 图标文件是否存在（可选）
        3. 桌面文件必需字段
        """
        errors = []

        config = self.get_format_config("appimage")

        # 检查 appimagetool 工具
        try:
            if not shutil.which("appimagetool"):
                errors.append(
                    "appimagetool 工具未安装\n"
                    "请安装: \n"
                    "  方法1: 从 https://github.com/AppImage/AppImageKit/releases 下载\n"
                    "  方法2: wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage -O /usr/local/bin/appimagetool && chmod +x /usr/local/bin/appimagetool"
                )
        except Exception:
            errors.append("无法检查 appimagetool 工具")

        # 检查图标文件（警告而非错误）
        icon_path = config.get("icon") or self.config.get("icon")
        if icon_path and not os.path.exists(icon_path):
            # 这里不添加到 errors，因为缺少图标不应该阻止构建
            # 但会在构建时发出警告
            pass

        # 检查必需的应用名称
        if not self.config.get("name"):
            errors.append("AppImage 配置缺少应用名称 (name)")

        return errors
