#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MacOS Info.plist 更新器 在 PyInstaller 构建完成后，更新 Info.plist 添加权限描述.
"""

import subprocess
from pathlib import Path
from typing import Any, Dict


class InfoPlistUpdater:
    """
    Info.plist 更新器.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def _print(self, message: str):
        """
        只在 verbose 模式下打印信息.
        """
        if self.verbose:
            print(message)

    # 配置键到 Info.plist 权限描述键的映射
    PERMISSION_MAPPING = {
        "microphone_usage_description": "NSMicrophoneUsageDescription",
        "camera_usage_description": "NSCameraUsageDescription",
        "speech_recognition_usage_description": "NSSpeechRecognitionUsageDescription",
        "local_network_usage_description": "NSLocalNetworkUsageDescription",
        "audio_usage_description": "NSAudioUsageDescription",
        "accessibility_usage_description": "NSAccessibilityUsageDescription",
        "documents_folder_usage_description": "NSDocumentsFolderUsageDescription",
        "downloads_folder_usage_description": "NSDownloadsFolderUsageDescription",
        "desktop_folder_usage_description": "NSDesktopFolderUsageDescription",
        "apple_events_usage_description": "NSAppleEventsUsageDescription",
        "system_administration_usage_description": "NSSystemAdministrationUsageDescription",
        "contacts_usage_description": "NSContactsUsageDescription",
        "calendars_usage_description": "NSCalendarsUsageDescription",
        "reminders_usage_description": "NSRemindersUsageDescription",
        "photo_library_usage_description": "NSPhotoLibraryUsageDescription",
        "photo_library_add_usage_description": "NSPhotoLibraryAddUsageDescription",
        "location_when_in_use_usage_description": "NSLocationWhenInUseUsageDescription",
        "location_always_and_when_in_use_usage_description": "NSLocationAlwaysAndWhenInUseUsageDescription",
        "bluetooth_always_usage_description": "NSBluetoothAlwaysUsageDescription",
        "bluetooth_peripheral_usage_description": "NSBluetoothPeripheralUsageDescription",
    }

    def update_app_info_plist(
        self, app_path: Path, macos_config: Dict[str, Any]
    ) -> bool:
        """更新 .app 包中的 Info.plist 文件.

        Args:
            app_path: .app 包路径
            macos_config: macOS 配置字典

        Returns:
            bool: 更新是否成功
        """
        if not app_path.exists() or not app_path.name.endswith(".app"):
            print(f"❌ 无效的 .app 包路径: {app_path}")  # 错误信息始终显示
            return False

        info_plist_path = app_path / "Contents" / "Info.plist"

        if not info_plist_path.exists():
            print(f"❌ Info.plist 不存在: {info_plist_path}")  # 错误信息始终显示
            return False

        self._print(f"🔧 更新 Info.plist 权限描述: {info_plist_path}")

        # 备份原始文件
        backup_path = info_plist_path.with_suffix(".plist.backup")
        try:
            import shutil

            shutil.copy2(info_plist_path, backup_path)
            self._print(f"✅ Info.plist 已备份: {backup_path}")
        except Exception as e:
            self._print(f"⚠️ 备份失败: {e}")

        success_count = 0
        total_permissions = 0

        # 添加权限描述
        for config_key, description in macos_config.items():
            if config_key in self.PERMISSION_MAPPING and description:
                plist_key = self.PERMISSION_MAPPING[config_key]

                if self._update_plist_permission(
                    info_plist_path, plist_key, description
                ):
                    success_count += 1
                    self._print(f"  ✅ {plist_key}: {description[:50]}...")
                else:
                    print(f"  ❌ {plist_key}: 更新失败")  # 错误信息始终显示

                total_permissions += 1

        # 添加一些特殊权限
        self._add_special_permissions(info_plist_path, macos_config)

        self._print(f"📋 权限描述更新完成: {success_count}/{total_permissions}")
        return success_count > 0

    def _update_plist_permission(
        self, plist_path: Path, key: str, description: str
    ) -> bool:
        """使用 PlistBuddy 更新单个权限描述.

        Args:
            plist_path: plist 文件路径
            key: 权限键
            description: 权限描述

        Returns:
            bool: 更新是否成功
        """
        try:
            # 尝试添加新键值
            add_cmd = [
                "/usr/libexec/PlistBuddy",
                "-c",
                f'Add :{key} string "{description}"',
                str(plist_path),
            ]

            result = subprocess.run(
                add_cmd, capture_output=True, text=True, check=False
            )

            # 如果添加失败（可能已存在），尝试更新
            if result.returncode != 0:
                set_cmd = [
                    "/usr/libexec/PlistBuddy",
                    "-c",
                    f'Set :{key} "{description}"',
                    str(plist_path),
                ]

                result = subprocess.run(
                    set_cmd, capture_output=True, text=True, check=False
                )

            return result.returncode == 0

        except Exception as e:
            print(f"❌ PlistBuddy 执行异常: {e}")  # 错误信息始终显示
            return False

    def _add_special_permissions(self, plist_path: Path, macos_config: Dict[str, Any]):
        """
        添加特殊权限配置.
        """

        # 添加后台音频权限（如果需要音频访问）
        if macos_config.get("audio_usage_description") or macos_config.get(
            "microphone_usage_description"
        ):
            try:
                # 创建 UIBackgroundModes 数组
                subprocess.run(
                    [
                        "/usr/libexec/PlistBuddy",
                        "-c",
                        "Add :UIBackgroundModes array",
                        str(plist_path),
                    ],
                    capture_output=True,
                    check=False,
                )

                # 添加 audio 模式
                subprocess.run(
                    [
                        "/usr/libexec/PlistBuddy",
                        "-c",
                        'Add :UIBackgroundModes:0 string "audio"',
                        str(plist_path),
                    ],
                    capture_output=True,
                    check=False,
                )

                self._print("  ✅ 添加后台音频权限")

            except Exception:
                pass  # 忽略错误，可能已存在

        # 添加音频会话类别
        if macos_config.get("audio_usage_description"):
            try:
                subprocess.run(
                    [
                        "/usr/libexec/PlistBuddy",
                        "-c",
                        "Add :AVAudioSessionCategoryPlayAndRecord bool true",
                        str(plist_path),
                    ],
                    capture_output=True,
                    check=False,
                )

                self._print("  ✅ 添加音频会话类别")

            except Exception:
                pass  # 忽略错误，可能已存在

    def list_app_permissions(self, app_path: Path) -> Dict[str, str]:
        """列出 .app 包中的所有权限描述.

        Args:
            app_path: .app 包路径

        Returns:
            Dict[str, str]: 权限键值对
        """
        info_plist_path = app_path / "Contents" / "Info.plist"

        if not info_plist_path.exists():
            return {}

        permissions = {}

        for plist_key in self.PERMISSION_MAPPING.values():
            try:
                cmd = [
                    "/usr/libexec/PlistBuddy",
                    "-c",
                    f"Print :{plist_key}",
                    str(info_plist_path),
                ]

                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False
                )

                if result.returncode == 0:
                    permissions[plist_key] = result.stdout.strip()

            except Exception:
                continue

        return permissions
