#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MacOS ZIP 打包器 创建ZIP格式的应用分发包.
"""

import os
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from ..base import BasePackager


class ZipPackager(BasePackager):
    """
    ZIP 打包器.
    """

    def get_supported_formats(self) -> List[str]:
        """
        获取支持的打包格式.
        """
        return ["zip"]

    def can_package_format(self, format_type: str) -> bool:
        """
        检查是否支持指定格式.
        """
        return format_type in self.get_supported_formats()

    def package(self, format_type: str, source_path: Path, output_path: Path) -> bool:
        """执行ZIP打包.

        Args:
            format_type: 打包格式 (zip)
            source_path: PyInstaller生成的应用路径
            output_path: 输出ZIP文件路径

        Returns:
            bool: 打包是否成功
        """
        if not self.can_package_format(format_type):
            self.progress.on_error(
                Exception(f"不支持的格式: {format_type}"), "macOS ZIP打包"
            )
            return False

        # 获取ZIP配置
        zip_config = self.get_format_config("zip")

        try:
            # 确保输出目录存在
            self.ensure_output_dir(output_path)

            # 创建ZIP文件
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:

                if source_path.is_file():
                    # 单个文件
                    self.progress.update_stage(
                        "macOS ZIP打包", 10, f"添加文件: {source_path.name}"
                    )
                    zipf.write(source_path, source_path.name)

                else:
                    # 目录 - 递归添加所有文件
                    total_files = sum(
                        len(files) for _, _, files in os.walk(source_path)
                    )
                    processed_files = 0

                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            file_path = Path(root) / file
                            # 计算在ZIP中的相对路径
                            arcname = file_path.relative_to(source_path.parent)

                            self.progress.update_stage(
                                "macOS ZIP打包",
                                int(70 * processed_files / total_files),
                                f"添加文件: {file}",
                            )

                            zipf.write(file_path, arcname)
                            processed_files += 1

                # 添加额外文件（如果配置了）
                self._add_extra_files(zipf, zip_config)

            self.progress.update_stage("macOS ZIP打包", 10, "验证ZIP文件")

            # 验证生成的ZIP文件
            if output_path.exists() and output_path.stat().st_size > 0:
                # 测试ZIP文件完整性
                with zipfile.ZipFile(output_path, "r") as zipf:
                    bad_file = zipf.testzip()
                    if bad_file:
                        self.progress.on_error(
                            Exception(f"ZIP文件损坏: {bad_file}"), "macOS ZIP打包"
                        )
                        return False

                return True
            else:
                self.progress.on_error(
                    Exception(f"ZIP文件生成失败: {output_path}"), "macOS ZIP打包"
                )
                return False

        except Exception as e:
            self.progress.on_error(Exception(f"ZIP打包失败: {e}"), "macOS ZIP打包")
            return False

    def _add_extra_files(self, zipf: zipfile.ZipFile, config: Dict[str, Any]):
        """
        添加额外的文件到ZIP包.
        """
        extra_files = config.get("extra_files", [])

        for extra_file in extra_files:
            if isinstance(extra_file, str):
                # 简单的文件路径
                if os.path.exists(extra_file):
                    zipf.write(extra_file, os.path.basename(extra_file))
            elif isinstance(extra_file, dict):
                # 带有映射的文件
                source = extra_file.get("source")
                target = (
                    extra_file.get("target", os.path.basename(source))
                    if source
                    else None
                )

                if source and target and os.path.exists(source):
                    zipf.write(source, target)

        # 添加README文件（如果配置了）
        readme_content = config.get("readme_content")
        if readme_content:
            zipf.writestr("README.txt", readme_content)

        # 添加许可证文件
        license_file = config.get("license_file")
        if license_file and os.path.exists(license_file):
            zipf.write(license_file, "LICENSE.txt")

    def validate_config(self, format_type: str) -> List[str]:
        """
        验证ZIP配置.
        """
        errors = []

        config = self.get_format_config("zip")

        # 检查额外文件
        extra_files = config.get("extra_files", [])
        for extra_file in extra_files:
            if isinstance(extra_file, str):
                if not os.path.exists(extra_file):
                    errors.append(f"额外文件不存在: {extra_file}")
            elif isinstance(extra_file, dict):
                source = extra_file.get("source")
                if source and not os.path.exists(source):
                    errors.append(f"额外文件不存在: {source}")

        # 检查许可证文件
        license_file = config.get("license_file")
        if license_file and not os.path.exists(license_file):
            errors.append(f"许可证文件不存在: {license_file}")

        return errors
