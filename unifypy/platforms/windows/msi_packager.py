#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Windows MSI packager (WiX Toolset MVP)."""

import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

from ..base import BasePackager


def _wix_tools_available() -> bool:
    return shutil.which("candle") is not None and shutil.which("light") is not None


def _xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def build_minimal_wxs(
    product_name: str,
    version: str,
    manufacturer: str,
    upgrade_code: str,
    component_guid: str,
    source_file: Path,
    install_name: str,
) -> str:
    """Generate a minimal WiX 3.x .wxs for a single executable."""
    product_name_x = _xml_escape(product_name)
    manufacturer_x = _xml_escape(manufacturer)
    version_x = _xml_escape(version)
    source_x = _xml_escape(str(source_file.resolve()))
    install_name_x = _xml_escape(install_name)

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*"
           Name="{product_name_x}"
           Language="1033"
           Version="{version_x}"
           Manufacturer="{manufacturer_x}"
           UpgradeCode="{upgrade_code}">
    <Package InstallerVersion="200" Compressed="yes" InstallScope="perMachine" />
    <MajorUpgrade DowngradeErrorMessage="A newer version is already installed." />
    <MediaTemplate EmbedCab="yes" />
    <Feature Id="ProductFeature" Title="{product_name_x}" Level="1">
      <ComponentGroupRef Id="ProductComponents" />
    </Feature>
  </Product>
  <Fragment>
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFilesFolder">
        <Directory Id="INSTALLFOLDER" Name="{product_name_x}" />
      </Directory>
    </Directory>
  </Fragment>
  <Fragment>
    <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">
      <Component Id="MainExecutable" Guid="{component_guid}">
        <File Id="MainExe"
              Source="{source_x}"
              Name="{install_name_x}"
              KeyPath="yes" />
      </Component>
    </ComponentGroup>
  </Fragment>
</Wix>
'''


class MSIPackager(BasePackager):
    """Minimal MSI packager using WiX candle/light."""

    def get_supported_formats(self) -> List[str]:
        return ["msi"]

    def can_package_format(self, format_type: str) -> bool:
        return format_type in self.get_supported_formats()

    def validate_config(self, format_type: str) -> List[str]:
        errors: List[str] = []
        if not _wix_tools_available():
            errors.append(
                "未找到 WiX Toolset（需要 PATH 中的 candle 与 light）。"
                "安装: https://wixtoolset.org/ 或 `choco install wixtoolset`，"
                "然后将 WiX bin 目录加入 PATH。"
            )
        if not self.config.get("name"):
            errors.append("缺少应用名称 name")
        if not self.config.get("version"):
            errors.append("缺少版本号 version")
        return errors

    def _resolve_main_exe(self, source_path: Path) -> Optional[Path]:
        """Pick main executable from onefile path or onedir folder."""
        app_name = self.config.get("name", "MyApp")
        if source_path.is_file():
            return source_path
        if not source_path.is_dir():
            return None
        candidates = [
            source_path / f"{app_name}.exe",
            source_path / app_name,
        ]
        for c in candidates:
            if c.is_file():
                return c
        # Fall back to first .exe in directory
        for p in sorted(source_path.glob("*.exe")):
            if p.is_file():
                return p
        return None

    def package(self, format_type: str, source_path: Path, output_path: Path) -> bool:
        if not self.can_package_format(format_type):
            self.progress.on_error(
                Exception(f"不支持的格式: {format_type}"), "Windows MSI打包"
            )
            return False

        if not _wix_tools_available():
            self.progress.on_error(
                Exception(
                    "未找到 WiX Toolset (candle/light)。"
                    "请安装 WiX 并确保 candle 与 light 在 PATH 中。"
                ),
                "Windows MSI打包",
            )
            return False

        main_exe = self._resolve_main_exe(source_path)
        if not main_exe:
            self.progress.on_error(
                Exception(f"无法定位主可执行文件: {source_path}"),
                "Windows MSI打包",
            )
            return False

        product_name = self.config.get("display_name") or self.config.get(
            "name", "MyApp"
        )
        version = self.config.get("version", "1.0.0")
        # WiX Product Version: up to 4 numeric parts; keep simple
        manufacturer = self.config.get("publisher", "Unknown")
        msi_cfg = self.get_format_config("msi") if hasattr(self, "get_format_config") else {}
        if not msi_cfg:
            msi_cfg = (
                self.config.get("platforms", {})
                .get("windows", {})
                .get("msi", {})
            )
        upgrade_code = msi_cfg.get("upgrade_code") or str(
            uuid.uuid5(uuid.NAMESPACE_DNS, f"unifypy.msi.{product_name}")
        )
        component_guid = msi_cfg.get("component_guid") or str(uuid.uuid4())

        wxs_content = build_minimal_wxs(
            product_name=product_name,
            version=version,
            manufacturer=manufacturer,
            upgrade_code=upgrade_code,
            component_guid=component_guid,
            source_file=main_exe,
            install_name=main_exe.name,
        )

        self.ensure_output_dir(output_path)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            wxs_path = temp_path / "product.wxs"
            wxs_path.write_text(wxs_content, encoding="utf-8")
            wixobj = temp_path / "product.wixobj"

            candle = shutil.which("candle")
            light = shutil.which("light")
            assert candle and light

            ok = self.runner.run_command(
                [candle, "-nologo", "-out", str(wixobj), str(wxs_path)],
                "Windows MSI打包",
                "WiX candle 编译...",
                40,
                shell=False,
            )
            if not ok:
                return False

            # light may write to output_path
            out = str(output_path)
            ok = self.runner.run_command(
                [light, "-nologo", "-out", out, str(wixobj)],
                "Windows MSI打包",
                "WiX light 链接...",
                40,
                shell=False,
            )
            if not ok:
                return False

            if output_path.exists():
                self.progress.info(f"MSI 已生成: {output_path}")
                return True
            self.progress.on_error(
                Exception(f"MSI 输出不存在: {output_path}"), "Windows MSI打包"
            )
            return False
