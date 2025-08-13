#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境管理器
处理构建环境的准备和清理
"""

import os
import platform
from typing import Dict, Any, Optional
from pathlib import Path


class EnvironmentManager:
    """环境管理器"""
    
    def __init__(self, project_dir: str):
        """
        初始化环境管理器
        
        Args:
            project_dir: 项目目录
        """
        self.project_dir = Path(project_dir).resolve()
        self.current_platform = self._detect_platform()
        self.current_arch = self._detect_architecture()
    
    def _detect_platform(self) -> str:
        """检测当前平台"""
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        else:
            return system
    
    def _detect_architecture(self) -> str:
        """检测当前架构"""
        machine = platform.machine().lower()
        if machine in ['x86_64', 'amd64']:
            return 'x86_64'
        elif machine in ['aarch64', 'arm64']:
            return 'arm64'
        elif machine in ['i386', 'i686']:
            return 'i386'
        else:
            return machine
    
    def get_platform_info(self) -> Dict[str, Any]:
        """
        获取平台信息
        
        Returns:
            Dict[str, Any]: 平台信息字典
        """
        return {
            'platform': self.current_platform,
            'architecture': self.current_arch,
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }
    
    def check_prerequisites(self) -> Dict[str, bool]:
        """
        检查构建前提条件
        
        Returns:
            Dict[str, bool]: 检查结果字典
        """
        results = {}
        
        # 检查Python版本
        import sys
        python_version = sys.version_info
        results['python_version'] = python_version >= (3, 6)
        
        # 检查PyInstaller
        try:
            import PyInstaller
            results['pyinstaller'] = True
        except ImportError:
            results['pyinstaller'] = False
        
        # 检查必要库
        try:
            import rich
            results['rich'] = True
        except ImportError:
            results['rich'] = False
        
        try:
            import requests
            results['requests'] = True
        except ImportError:
            results['requests'] = False
        
        return results
    
    def get_recommended_settings(self) -> Dict[str, Any]:
        """
        获取推荐的平台设置
        
        Returns:
            Dict[str, Any]: 推荐设置
        """
        settings = {}
        
        if self.current_platform == "windows":
            settings.update({
                'pyinstaller': {
                    'windowed': True,
                    'icon': 'app.ico'
                },
                'installer_type': 'inno_setup'
            })
        elif self.current_platform == "macos":
            settings.update({
                'pyinstaller': {
                    'windowed': True,
                    'osx_bundle_identifier': 'com.example.app'
                },
                'installer_type': 'dmg'
            })
        elif self.current_platform == "linux":
            settings.update({
                'pyinstaller': {
                    'strip': True
                },
                'installer_type': 'deb'
            })
        
        return settings