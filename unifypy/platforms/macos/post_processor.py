#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
macOS 后处理器
负责 macOS 平台特定的构建后处理操作
"""

from unifypy.core.platforms import normalize_platform
from pathlib import Path
from typing import Optional


class MacOSPostProcessor:
    """
    macOS 平台后处理器.
    处理 Info.plist 更新、代码签名等 macOS 特定操作.
    """

    def __init__(
        self,
        info_plist_updater,
        macos_codesigner,
        pyinstaller_builder,
        verbose: bool = False
    ):
        """
        初始化 macOS 后处理器.

        Args:
            info_plist_updater: Info.plist 更新器实例
            macos_codesigner: macOS 代码签名器实例
            pyinstaller_builder: PyInstaller 配置构建器实例
            verbose: 是否显示详细信息
        """
        self.info_plist_updater = info_plist_updater
        self.macos_codesigner = macos_codesigner
        self.pyinstaller_builder = pyinstaller_builder
        self.verbose = verbose

    def is_macos(self) -> bool:
        """
        检查当前是否为 macOS 平台.

        Returns:
            bool: 是否为 macOS
        """
        return normalize_platform() == "macos"

    def prepare_entitlements_config(
        self,
        config,
        project_dir: Path,
        args
    ) -> dict:
        """
        准备 macOS entitlements 配置（构建前处理）.

        Args:
            config: ConfigManager 实例
            project_dir: 项目目录
            args: 命令行参数

        Returns:
            dict: 更新后的配置字典（如果有变化）
        """
        if not self.is_macos():
            return {}

        # 判断是否为开发版本（默认开启，适用于未签名应用）
        # 只有明确指定 --production 时才禁用开发模式
        production = getattr(args, "production", False)
        development = (
            not production
            or getattr(args, "development", False)
            or getattr(args, "debug", False)
        )

        # 更新配置以包含自动生成的 entitlements
        # 注意：传递原始配置以保持 platforms 结构
        updated_config = (
            self.pyinstaller_builder.update_config_with_auto_entitlements(
                config.raw_config, project_dir, development
            )
        )

        return updated_config

    def process_built_app(
        self,
        app_name: str,
        dist_dir: Path,
        config,
        project_dir: Path
    ) -> bool:
        """
        处理构建完成的 .app 包（构建后处理）.

        Args:
            app_name: 应用名称
            dist_dir: 输出目录
            config: ConfigManager 实例
            project_dir: 项目目录

        Returns:
            bool: 是否处理成功
        """
        if not self.is_macos():
            return True  # 非 macOS 平台，无需处理

        # 查找 .app 包
        app_path = dist_dir / f"{app_name}.app"

        if not app_path.exists():
            print(f"⚠️ 未找到 .app 包: {app_path}")
            return False

        # 更新 Info.plist
        if not self._update_info_plist(app_path, config):
            return False

        # 执行代码签名
        self._sign_app(app_path, project_dir)

        return True

    def _update_info_plist(self, app_path: Path, config) -> bool:
        """
        更新 macOS .app 包中的 Info.plist 权限描述.

        Args:
            app_path: .app 包路径
            config: ConfigManager 实例

        Returns:
            bool: 是否更新成功
        """
        try:
            # 获取 macOS 配置
            macos_config = config._get_platform_config().get("macos", {})
            if not macos_config:
                # 从原始配置获取
                raw_config = getattr(config, "raw_config", {})
                if "platforms" in raw_config:
                    macos_config = raw_config["platforms"].get("macos", {})

            if not macos_config:
                if self.verbose:
                    print("⚠️ 未找到 macOS 平台配置")
                return True  # 没有配置不算失败

            if self.verbose:
                print("🔧 更新 macOS 权限描述...")

            success = self.info_plist_updater.update_app_info_plist(
                app_path, macos_config
            )

            if success:
                if self.verbose:
                    print("✅ Info.plist 权限描述更新完成")

                    # 显示已添加的权限
                    permissions = self.info_plist_updater.list_app_permissions(
                        app_path
                    )
                    if permissions:
                        print("📋 已配置的权限描述:")
                        for key, desc in permissions.items():
                            print(f"  • {key}: {desc[:60]}...")
            else:
                print("⚠️ Info.plist 权限描述更新失败")  # 错误信息始终显示

            return success

        except Exception as e:
            print(f"❌ Info.plist 更新异常: {e}")
            return False

    def _sign_app(self, app_path: Path, project_dir: Path):
        """
        对 macOS .app 包执行 ad-hoc 代码签名以应用 entitlements.

        Args:
            app_path: .app 包路径
            project_dir: 项目目录
        """
        try:
            if self.verbose:
                print(f"🔐 准备对 {app_path.name} 执行代码签名...")

            # 检查 codesign 工具是否可用
            if not self.macos_codesigner.check_codesign_available():
                print("⚠️ codesign 工具不可用，跳过代码签名")  # 错误信息始终显示
                return

            # 查找 entitlements.plist 文件
            entitlements_path = self._find_entitlements_file(
                app_path, project_dir
            )

            # 执行签名
            success = self.macos_codesigner.sign_app_with_entitlements(
                app_path, entitlements_path
            )

            if success:
                if self.verbose:
                    print("✅ macOS 代码签名完成，权限应该已生效")
            else:
                print("⚠️ 代码签名失败，但应用仍可正常使用")  # 警告信息始终显示

        except Exception as e:
            print(f"❌ macOS 代码签名异常: {e}")

    def _find_entitlements_file(
        self,
        app_path: Path,
        project_dir: Path
    ) -> Optional[Path]:
        """
        查找 entitlements.plist 文件.

        Args:
            app_path: .app 包路径
            project_dir: 项目目录

        Returns:
            Optional[Path]: entitlements 文件路径，如果未找到则返回 None
        """
        # 首先检查项目根目录
        project_entitlements = project_dir / "entitlements.plist"
        if project_entitlements.exists():
            if self.verbose:
                print(f"📜 找到 entitlements 文件: {project_entitlements}")
            return project_entitlements

        # 如果没找到，检查 .app 包内的 entitlements
        app_entitlements = app_path / "Contents" / "entitlements.plist"
        if app_entitlements.exists():
            if self.verbose:
                print(f"📜 使用 .app 包内的 entitlements: {app_entitlements}")
            return app_entitlements

        return None

    def print_debug_info(self, command: list):
        """
        打印 PyInstaller 命令的调试信息（仅在 verbose 模式）.

        Args:
            command: PyInstaller 命令列表
        """
        if not self.verbose or not self.is_macos():
            return

        print("\n🔍 PyInstaller 命令调试:")
        print(f"完整命令: {' '.join(command)}")

        # 检查关键参数
        if "--osx-bundle-identifier" in command:
            idx = command.index("--osx-bundle-identifier")
            if idx + 1 < len(command):
                print(f"  Bundle ID: {command[idx + 1]}")

        if "--osx-entitlements-file" in command:
            idx = command.index("--osx-entitlements-file")
            if idx + 1 < len(command):
                entitlements_path = command[idx + 1]
                print(f"  Entitlements: {entitlements_path}")
                print(f"  文件存在: {Path(entitlements_path).exists()}")

        print()
