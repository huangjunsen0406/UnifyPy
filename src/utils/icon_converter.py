#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化的图标格式转换工具
支持基本的 PNG -> ICNS 转换
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional


class IconConverter:
    """简化的图标格式转换器"""
    
    def ensure_icon_format(self, icon_path: str, target_format: str, project_dir: Path) -> Optional[str]:
        """
        确保图标是指定格式，如果不是则转换
        
        Args:
            icon_path: 图标路径（相对或绝对）
            target_format: 目标格式 ('icns', 'ico', 'png')  
            project_dir: 项目目录
            
        Returns:
            Optional[str]: 最终的图标路径，失败返回 None
        """
        if not icon_path:
            return None
        
        # 解析路径
        if os.path.isabs(icon_path):
            source_path = Path(icon_path)
        else:
            source_path = project_dir / icon_path
        
        if not source_path.exists():
            print(f"❌ 图标文件不存在: {source_path}")
            return None
        
        # 检查是否已经是目标格式
        current_ext = source_path.suffix.lower()
        target_ext = f".{target_format.lower()}"
        
        if current_ext == target_ext:
            return str(source_path)
        
        # 对于 macOS，如果是 PNG 转 ICNS，尝试转换
        if target_format.lower() == 'icns' and current_ext == '.png':
            target_path = source_path.parent / f"{source_path.stem}.icns"
            
            if self._convert_png_to_icns(source_path, target_path):
                return str(target_path)
        
        # 如果转换失败或不支持，返回原始路径
        print(f"ℹ️  使用原始图标格式: {source_path}")
        return str(source_path)
    
    def _convert_png_to_icns(self, png_path: Path, icns_path: Path) -> bool:
        """
        使用 macOS 系统工具将 PNG 转换为 ICNS
        
        Args:
            png_path: 源 PNG 文件
            icns_path: 目标 ICNS 文件
            
        Returns:
            bool: 转换是否成功
        """
        try:
            # 创建临时 iconset 目录
            with tempfile.TemporaryDirectory() as temp_dir:
                iconset_dir = Path(temp_dir) / "icon.iconset"
                iconset_dir.mkdir()
                
                # 生成标准尺寸
                sizes = [16, 32, 64, 128, 256, 512, 1024]
                
                for size in sizes:
                    # 标准分辨率
                    target_file = iconset_dir / f"icon_{size}x{size}.png"
                    if not self._resize_with_sips(png_path, target_file, size):
                        print(f"❌ 生成 {size}x{size} 图标失败")
                        return False
                    
                    # 高分辨率版本（@2x，除了 1024px）
                    if size < 1024:
                        target_file_2x = iconset_dir / f"icon_{size}x{size}@2x.png"  
                        if not self._resize_with_sips(png_path, target_file_2x, size * 2):
                            print(f"❌ 生成 {size}x{size}@2x 图标失败")
                
                # 使用 iconutil 转换为 ICNS
                cmd = ['iconutil', '-c', 'icns', str(iconset_dir), '-o', str(icns_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                
                if result.returncode == 0:
                    print(f"✅ 图标转换成功: {png_path.name} -> {icns_path.name}")
                    return True
                else:
                    print(f"❌ iconutil 执行失败: {result.stderr}")
                    return False
                    
        except Exception as e:
            print(f"❌ 图标转换异常: {e}")
            return False
    
    def _resize_with_sips(self, source: Path, target: Path, size: int) -> bool:
        """使用 sips 调整图像大小"""
        try:
            cmd = ['sips', '-z', str(size), str(size), str(source), '--out', str(target)]
            result = subprocess.run(cmd, capture_output=True, check=False)
            return result.returncode == 0
        except Exception:
            return False