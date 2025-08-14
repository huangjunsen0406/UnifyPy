#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MacOS PKG 打包器 使用pkgbuild和productbuild创建PKG安装包.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from ..base import BasePackager


class PKGPackager(BasePackager):
    """
    PKG 打包器.
    """

    def get_supported_formats(self) -> List[str]:
        """
        获取支持的打包格式.
        """
        return ["pkg"]

    def can_package_format(self, format_type: str) -> bool:
        """
        检查是否支持指定格式.
        """
        return format_type in self.get_supported_formats()

    def package(self, format_type: str, source_path: Path, output_path: Path) -> bool:
        """执行PKG打包.

        Args:
            format_type: 打包格式 (pkg)
            source_path: PyInstaller生成的应用路径
            output_path: 输出PKG文件路径

        Returns:
            bool: 打包是否成功
        """
        if not self.can_package_format(format_type):
            self.progress.on_error(
                Exception(f"不支持的格式: {format_type}"), "macOS PKG打包"
            )
            return False

        # 获取PKG配置
        pkg_config = self.get_format_config("pkg")

        # 确保源路径是.app格式
        if source_path.is_file():
            # 如果是单个文件，需要先创建.app包
            from .dmg_packager import DMGPackager

            dmg_packager = DMGPackager(
                self.progress, self.runner, self.tool_manager, self.config
            )
            app_path = dmg_packager._create_app_bundle(source_path, pkg_config)
            if not app_path:
                return False
        else:
            app_path = source_path

        # 创建临时目录用于构建
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            component_pkg = temp_path / "component.pkg"

            # 第一步：使用pkgbuild创建组件包
            pkgbuild_cmd = [
                "pkgbuild",
                "--root",
                str(app_path.parent),
                "--identifier",
                pkg_config.get(
                    "identifier", f'com.example.{self.config.get("name", "MyApp")}'
                ),
                "--version",
                self.config.get("version", "1.0.0"),
                "--install-location",
                "/Applications",
                str(component_pkg),
            ]

            # 添加脚本支持
            scripts_dir = pkg_config.get("scripts_dir")
            if scripts_dir and os.path.exists(scripts_dir):
                pkgbuild_cmd.extend(["--scripts", scripts_dir])

            success = self.runner.run_command(
                pkgbuild_cmd, "macOS PKG打包", "创建组件包...", 40, shell=False
            )

            if not success:
                return False

            # 第二步：使用productbuild创建最终的PKG
            if pkg_config.get("use_distribution", True):
                # 创建分发定义文件
                distribution_xml = self._create_distribution_xml(
                    pkg_config, component_pkg
                )
                distribution_file = temp_path / "distribution.xml"

                with open(distribution_file, "w", encoding="utf-8") as f:
                    f.write(distribution_xml)

                productbuild_cmd = [
                    "productbuild",
                    "--distribution",
                    str(distribution_file),
                    "--package-path",
                    str(temp_path),
                    str(output_path),
                ]
            else:
                # 简单模式
                productbuild_cmd = [
                    "productbuild",
                    "--component",
                    str(app_path),
                    "/Applications",
                    str(output_path),
                ]

            # 添加签名支持
            sign_identity = pkg_config.get("sign_identity")
            if sign_identity:
                productbuild_cmd.extend(["--sign", sign_identity])

            success = self.runner.run_command(
                productbuild_cmd,
                "macOS PKG打包",
                "生成最终PKG安装包...",
                40,
                shell=False,
            )

            if success and output_path.exists():
                return True
            else:
                self.progress.on_error(
                    Exception(f"PKG文件生成失败: {output_path}"), "macOS PKG打包"
                )
                return False

    def _create_distribution_xml(
        self, config: Dict[str, Any], component_pkg: Path
    ) -> str:
        """
        创建分发定义XML文件.
        """
        app_name = self.config.get("name", "MyApp")
        app_version = self.config.get("version", "1.0.0")
        publisher = self.config.get("publisher", "Unknown Publisher")

        # 基本的分发XML模板
        distribution_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>{app_name}</title>
    <organization>{publisher}</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="false"/>
    
    <!-- 定义包引用 -->
    <pkg-ref id="{config.get('identifier', f'com.example.{app_name.lower()}')}"/>
    
    <!-- 选择项 -->
    <choices-outline>
        <line choice="default">
            <line choice="{app_name}"/>
        </line>
    </choices-outline>
    
    <choice id="default"/>
    <choice id="{app_name}" visible="false">
        <pkg-ref id="{config.get('identifier', f'com.example.{app_name.lower()}')}"/>
    </choice>
    
    <!-- 包定义 -->
    <pkg-ref id="{config.get('identifier', f'com.example.{app_name.lower()}')}" 
             version="{app_version}" 
             onConclusion="none">
        {component_pkg.name}
    </pkg-ref>
"""

        # 添加许可协议
        license_file = config.get("license")
        if license_file and os.path.exists(license_file):
            distribution_xml += f"""
    <!-- 许可协议 -->
    <license file="{license_file}"/>
"""

        # 添加欢迎信息
        welcome_file = config.get("welcome")
        if welcome_file and os.path.exists(welcome_file):
            distribution_xml += f"""
    <!-- 欢迎信息 -->
    <welcome file="{welcome_file}"/>
"""

        # 添加自述信息
        readme_file = config.get("readme")
        if readme_file and os.path.exists(readme_file):
            distribution_xml += f"""
    <!-- 自述信息 -->
    <readme file="{readme_file}"/>
"""

        # 系统要求
        min_os_version = config.get("min_os_version", "10.9")
        distribution_xml += f"""
    <!-- 系统要求 -->
    <installation-check script="pm_install_check();"/>
    <script>
    <![CDATA[
        function pm_install_check() {{
            if(!(system.compareVersions(system.version.ProductVersion, '{min_os_version}') >= 0)) {{
                my.result.title = 'Unable to install';
                my.result.message = 'This software requires Mac OS X {min_os_version} or later.';
                my.result.type = 'Fatal';
                return false;
            }}
            return true;
        }}
    ]]>
    </script>
"""

        distribution_xml += """
</installer-gui-script>"""

        return distribution_xml

    def validate_config(self, format_type: str) -> List[str]:
        """
        验证PKG配置.
        """
        errors = []

        config = self.get_format_config("pkg")

        # 检查脚本目录
        scripts_dir = config.get("scripts_dir")
        if scripts_dir and not os.path.exists(scripts_dir):
            errors.append(f"脚本目录不存在: {scripts_dir}")

        # 检查许可证文件
        license_file = config.get("license")
        if license_file and not os.path.exists(license_file):
            errors.append(f"许可证文件不存在: {license_file}")

        # 检查欢迎文件
        welcome_file = config.get("welcome")
        if welcome_file and not os.path.exists(welcome_file):
            errors.append(f"欢迎文件不存在: {welcome_file}")

        # 检查自述文件
        readme_file = config.get("readme")
        if readme_file and not os.path.exists(readme_file):
            errors.append(f"自述文件不存在: {readme_file}")

        return errors
