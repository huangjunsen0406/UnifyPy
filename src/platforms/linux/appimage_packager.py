#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Linux AppImage 打包器
创建便携式AppImage格式应用
"""

import os
import tempfile
import shutil
from typing import Dict, Any, List
from pathlib import Path
from ..base import BasePackager


class AppImagePackager(BasePackager):
    """AppImage 打包器"""
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的打包格式"""
        return ["appimage"]
    
    def can_package_format(self, format_type: str) -> bool:
        """检查是否支持指定格式"""
        return format_type in self.get_supported_formats()
    
    def package(self, format_type: str, source_path: Path, output_path: Path) -> bool:
        """
        执行AppImage打包
        
        Args:
            format_type: 打包格式 (appimage)
            source_path: PyInstaller生成的应用路径
            output_path: 输出AppImage文件路径
            
        Returns:
            bool: 打包是否成功
        """
        if not self.can_package_format(format_type):
            self.progress.on_error(
                Exception(f"不支持的格式: {format_type}"),
                "Linux AppImage打包"
            )
            return False
        
        # 确保appimagetool可用
        appimagetool_path = self.tool_manager.ensure_tool('appimagetool')
        if not appimagetool_path:
            self.progress.on_error(
                Exception("无法获取appimagetool工具"),
                "Linux AppImage打包"
            )
            return False
        
        # 获取AppImage配置
        appimage_config = self.get_format_config("appimage")
        
        # 创建临时AppDir
        with tempfile.TemporaryDirectory() as temp_dir:
            appdir_path = Path(temp_dir) / "AppDir"
            
            # 创建AppDir结构
            success = self._create_appdir(source_path, appdir_path, appimage_config)
            if not success:
                return False
            
            # 构建AppImage
            success = self._build_appimage(appdir_path, output_path, appimagetool_path, appimage_config)
            
            return success
    
    def _create_appdir(self, source_path: Path, appdir_path: Path, config: Dict[str, Any]) -> bool:
        """创建AppDir目录结构"""
        try:
            app_name = self.config.get('name', 'myapp')
            
            # 创建基本目录结构
            appdir_path.mkdir()
            (appdir_path / "usr" / "bin").mkdir(parents=True)
            (appdir_path / "usr" / "lib").mkdir(parents=True)
            (appdir_path / "usr" / "share" / "applications").mkdir(parents=True)
            (appdir_path / "usr" / "share" / "pixmaps").mkdir(parents=True)
            
            # 复制应用文件
            if source_path.is_file():
                # 单个可执行文件
                shutil.copy2(source_path, appdir_path / "usr" / "bin" / app_name)
                (appdir_path / "usr" / "bin" / app_name).chmod(0o755)
            else:
                # 目录 - 复制所有内容
                for item in source_path.iterdir():
                    if item.is_file():
                        shutil.copy2(item, appdir_path / "usr" / "bin")
                    else:
                        shutil.copytree(item, appdir_path / "usr" / "lib" / item.name)
                
                # 确保主可执行文件存在
                main_executable = appdir_path / "usr" / "bin" / app_name
                if not main_executable.exists():
                    # 查找可执行文件
                    for item in (appdir_path / "usr" / "bin").iterdir():
                        if item.is_file() and os.access(item, os.X_OK):
                            shutil.copy2(item, main_executable)
                            break
            
            # 创建桌面文件
            self._create_desktop_file(appdir_path, config)
            
            # 复制图标
            self._copy_icon(appdir_path, config)
            
            # 创建AppRun脚本
            self._create_apprun_script(appdir_path, config)
            
            self.progress.update_stage("Linux AppImage打包", 20, "AppDir结构创建完成")
            return True
            
        except Exception as e:
            self.progress.on_error(
                Exception(f"创建AppDir失败: {e}"),
                "Linux AppImage打包"
            )
            return False
    
    def _create_desktop_file(self, appdir_path: Path, config: Dict[str, Any]):
        """创建桌面文件"""
        app_name = self.config.get('name', 'myapp')
        display_name = self.config.get('display_name', app_name)
        
        # 桌面文件内容
        desktop_content = f"""[Desktop Entry]
Type=Application
Name={display_name}
Exec={app_name}
Icon={app_name}
Comment={config.get('description', display_name)}
Categories={config.get('categories', 'Utility;')}
Terminal={str(config.get('terminal', False)).lower()}
X-AppImage-Version={self.config.get('version', '1.0.0')}
"""
        
        # 写入桌面文件
        desktop_file = appdir_path / "usr" / "share" / "applications" / f"{app_name}.desktop"
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        
        # 也在根目录创建一个副本（AppImage标准）
        shutil.copy2(desktop_file, appdir_path / f"{app_name}.desktop")
    
    def _copy_icon(self, appdir_path: Path, config: Dict[str, Any]):
        """复制图标文件"""
        app_name = self.config.get('name', 'myapp')
        icon_path = config.get('icon') or self.config.get('icon')
        
        if icon_path and os.path.exists(icon_path):
            icon_ext = Path(icon_path).suffix
            
            # 复制到pixmaps目录
            icon_dest = appdir_path / "usr" / "share" / "pixmaps" / f"{app_name}{icon_ext}"
            shutil.copy2(icon_path, icon_dest)
            
            # 也在根目录创建一个副本（AppImage标准）
            shutil.copy2(icon_path, appdir_path / f"{app_name}{icon_ext}")
        else:
            # 创建默认图标
            self._create_default_icon(appdir_path / f"{app_name}.png")
    
    def _create_default_icon(self, icon_path: Path):
        """创建默认图标"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # 创建64x64的PNG图标
            size = (64, 64)
            image = Image.new('RGBA', size, (70, 130, 180, 255))  # 钢蓝色
            draw = ImageDraw.Draw(image)
            
            # 绘制简单的应用图标
            draw.rectangle([8, 8, 56, 56], outline=(255, 255, 255, 255), width=3)
            draw.text((16, 24), "App", fill=(255, 255, 255, 255))
            
            # 保存为PNG格式
            image.save(icon_path, format='PNG')
            
        except ImportError:
            # 如果PIL不可用，创建一个空的PNG文件
            # 最小有效PNG文件
            png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00@\x00\x00\x00@\x08\x06\x00\x00\x00\xaaiq\xde\x00\x00\x00\x19tEXtSoftware\x00Adobe ImageReadyq\xc9e<\x00\x00\x03(IDATx\xdab\xfc\x0f\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82'
            with open(icon_path, 'wb') as f:
                f.write(png_data)
    
    def _create_apprun_script(self, appdir_path: Path, config: Dict[str, Any]):
        """创建AppRun启动脚本"""
        app_name = self.config.get('name', 'myapp')
        
        apprun_content = f"""#!/bin/bash
# AppRun script for {app_name}

HERE="$(dirname "$(readlink -f "${{BASH_SOURCE[0]}}")")"

# 设置LD_LIBRARY_PATH
export LD_LIBRARY_PATH="$HERE/usr/lib:$LD_LIBRARY_PATH"

# 设置PATH
export PATH="$HERE/usr/bin:$PATH"

# 运行应用程序
exec "$HERE/usr/bin/{app_name}" "$@"
"""
        
        # 写入AppRun脚本
        apprun_file = appdir_path / "AppRun"
        with open(apprun_file, 'w') as f:
            f.write(apprun_content)
        apprun_file.chmod(0o755)
    
    def _build_appimage(self, appdir_path: Path, output_path: Path, appimagetool_path: str, config: Dict[str, Any]) -> bool:
        """构建AppImage文件"""
        # 确保输出目录存在
        self.ensure_output_dir(output_path)
        
        # 构建命令
        command = [appimagetool_path]
        
        # 添加选项
        if config.get('no_appstream', True):
            command.append('--no-appstream')
        
        if config.get('verbose', False):
            command.append('--verbose')
        
        # 压缩选项
        compression = config.get('compression')
        if compression:
            command.extend(['--comp', compression])
        
        # 添加AppDir和输出文件
        command.extend([str(appdir_path), str(output_path)])
        
        # 设置环境变量
        env = os.environ.copy()
        env['ARCH'] = self._get_arch()
        
        success = self.runner.run_command(
            command,
            "Linux AppImage打包",
            "正在生成AppImage文件...",
            60,
            shell=False
        )
        
        if success and output_path.exists():
            # 设置可执行权限
            output_path.chmod(0o755)
            return True
        else:
            self.progress.on_error(
                Exception(f"AppImage文件生成失败: {output_path}"),
                "Linux AppImage打包"
            )
            return False
    
    def _get_arch(self) -> str:
        """获取架构标识"""
        import platform
        arch = platform.machine()
        if arch == "x86_64":
            return "x86_64"
        elif arch.startswith("arm"):
            return "aarch64" if "64" in arch else "armhf"
        else:
            return arch
    
    def validate_config(self, format_type: str) -> List[str]:
        """验证AppImage配置"""
        errors = []
        
        config = self.get_format_config("appimage")
        
        # 检查图标文件
        icon_path = config.get('icon') or self.config.get('icon')
        if icon_path and not os.path.exists(icon_path):
            errors.append(f"图标文件不存在: {icon_path}")
        
        return errors