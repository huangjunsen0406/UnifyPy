#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows MSI 打包器 使用WiX工具集生成MSI安装包.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from ..base import BasePackager


class MSIPackager(BasePackager):
    """
    MSI 打包器.
    """

    def get_supported_formats(self) -> List[str]:
        """
        获取支持的打包格式.
        """
        return ["msi"]

    def can_package_format(self, format_type: str) -> bool:
        """
        检查是否支持指定格式.
        """
        return format_type in self.get_supported_formats()

    def package(self, format_type: str, source_path: Path, output_path: Path) -> bool:
        """执行MSI打包.

        Args:
            format_type: 打包格式 (msi)
            source_path: PyInstaller生成的可执行文件路径
            output_path: 输出MSI文件路径

        Returns:
            bool: 打包是否成功
        """
        if not self.can_package_format(format_type):
            self.progress.on_error(
                Exception(f"不支持的格式: {format_type}"), "Windows MSI打包"
            )
            return False

        # 检查WiX工具
        if not self._check_wix_tools():
            self.progress.on_error(
                Exception("未找到WiX工具集"),
                "Windows MSI打包",
                "请安装WiX工具集: https://wixtoolset.org/",
            )
            return False

        # 获取MSI配置
        msi_config = self.get_format_config("msi")

        # 创建WXS文件
        wxs_content = self._build_wxs_file(msi_config, source_path, output_path)

        # 创建临时文件
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            wxs_file = temp_path / "installer.wxs"
            wixobj_file = temp_path / "installer.wixobj"

            # 写入WXS文件
            with open(wxs_file, "w", encoding="utf-8") as f:
                f.write(wxs_content)

            # 编译WXS到WIXOBJ
            candle_cmd = ["candle", "-out", str(wixobj_file), str(wxs_file)]

            success = self.runner.run_command(
                candle_cmd, "Windows MSI打包", "编译WiX源文件...", 40, shell=False
            )

            if not success:
                return False

            # 链接生成MSI
            light_cmd = ["light", "-out", str(output_path), str(wixobj_file)]

            success = self.runner.run_command(
                light_cmd, "Windows MSI打包", "生成MSI安装包...", 40, shell=False
            )

            if success and output_path.exists():
                return True
            else:
                self.progress.on_error(
                    Exception(f"MSI文件生成失败: {output_path}"), "Windows MSI打包"
                )
                return False

    def _check_wix_tools(self) -> bool:
        """
        检查WiX工具是否可用.
        """
        try:
            import shutil

            return (
                shutil.which("candle.exe") is not None
                and shutil.which("light.exe") is not None
            )
        except:
            return False

    def _build_wxs_file(
        self, config: Dict[str, Any], source_path: Path, output_path: Path
    ) -> str:
        """
        构建WiX源文件.
        """
        app_name = self.config.get("name", "MyApp")
        app_version = self.config.get("version", "1.0.0")
        publisher = self.config.get("publisher", "Unknown Publisher")

        # 生成GUID
        import uuid

        product_id = str(uuid.uuid4()).upper()
        upgrade_code = str(uuid.uuid4()).upper()

        # 构建WXS内容
        wxs_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="{product_id}" 
           Name="{app_name}" 
           Language="1033" 
           Version="{app_version}" 
           Manufacturer="{publisher}" 
           UpgradeCode="{upgrade_code}">
    
    <Package InstallerVersion="200" 
             Compressed="yes" 
             InstallScope="perMachine" />
    
    <MajorUpgrade DowngradeErrorMessage="A newer version of {app_name} is already installed." />
    
    <MediaTemplate EmbedCab="yes" />
    
    <Feature Id="ProductFeature" Title="{app_name}" Level="1">
      <ComponentGroupRef Id="ProductComponents" />
    </Feature>
  </Product>
  
  <Fragment>
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLFOLDER" Name="{app_name}" />
      </Directory>
    </Directory>
  </Fragment>
  
  <Fragment>
    <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">"""

        if source_path.is_file():
            # 单文件模式
            file_id = "MainExecutable"
            wxs_content += f"""
      <Component Id="{file_id}" Guid="{str(uuid.uuid4()).upper()}">
        <File Id="{file_id}" Source="{source_path}" KeyPath="yes" />
      </Component>"""
        else:
            # 目录模式 - 递归添加所有文件
            component_id = 0
            for root, dirs, files in os.walk(source_path):
                for file in files:
                    file_path = Path(root) / file
                    file_path.relative_to(source_path)
                    component_id += 1

                    wxs_content += f"""
      <Component Id="Component{component_id}" Guid="{str(uuid.uuid4()).upper()}">
        <File Id="File{component_id}" Source="{file_path}" KeyPath="yes" />
      </Component>"""

        wxs_content += """
    </ComponentGroup>
  </Fragment>
</Wix>"""

        return wxs_content

    def validate_config(self, format_type: str) -> List[str]:
        """
        验证MSI配置.
        """
        errors = []

        # 检查WiX工具
        if not self._check_wix_tools():
            errors.append("未安装WiX工具集，请从 https://wixtoolset.org/ 下载安装")

        return errors
