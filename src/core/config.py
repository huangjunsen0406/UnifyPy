#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理系统
处理配置文件加载、合并和验证
"""

import json
import os
import platform
from typing import Dict, Any, Optional, List
from pathlib import Path


class ConfigManager:
    """配置管理器，处理配置合并和验证"""
    
    def __init__(self, config_path: Optional[str] = None, args: Optional[Dict] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
            args: 命令行参数字典
        """
        self.config_path = config_path
        self.args = args or {}
        self.raw_config = {}
        self.merged_config = {}
        self.current_platform = self._detect_platform()
        
        if config_path:
            self.raw_config = self._load_config(config_path)
        
        self.merged_config = self._merge_all_configs()
        self._validate_config()
    
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
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        加载JSON配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 配置字典
            
        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: 配置文件格式错误
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                config = json.load(f)
                return config
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"配置文件格式错误: {e}", e.doc, e.pos)
        except Exception as e:
            raise Exception(f"加载配置文件失败: {e}")
    
    def _merge_all_configs(self) -> Dict[str, Any]:
        """
        合并所有配置源
        优先级: 命令行参数 > 平台特定配置 > 全局配置 > 默认配置
        
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        # 默认配置
        default_config = self._get_default_config()
        
        # 从原始配置开始
        merged = default_config.copy()
        
        # 合并文件配置的全局部分
        if self.raw_config:
            global_config = {k: v for k, v in self.raw_config.items() 
                           if k not in ['platform_specific', 'platforms']}
            merged.update(global_config)
        
        # 合并平台特定配置
        platform_config = self._get_platform_config()
        if platform_config:
            merged.update(platform_config)
        
        # 合并命令行参数
        if self.args:
            args_config = self._args_to_config(self.args)
            merged.update(args_config)
        
        return merged
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "name": "UnknownApp",
            "version": "1.0.0",
            "entry": "main.py",
            "publisher": "Unknown Publisher",
            "onefile": False,
            "skip_installer": False,
            "pyinstaller": {
                "clean": True,
                "noconfirm": True
            }
        }
    
    def _get_platform_config(self) -> Dict[str, Any]:
        """
        获取当前平台的特定配置
        
        Returns:
            Dict[str, Any]: 平台特定配置
        """
        if not self.raw_config:
            return {}
        
        # 尝试新格式 (platforms)
        platforms = self.raw_config.get('platforms', {})
        if self.current_platform in platforms:
            return platforms[self.current_platform]
        
        # 尝试旧格式 (platform_specific)
        platform_specific = self.raw_config.get('platform_specific', {})
        if self.current_platform in platform_specific:
            return platform_specific[self.current_platform]
        
        return {}
    
    def _args_to_config(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        将命令行参数转换为配置格式
        
        Args:
            args: 命令行参数字典
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        config = {}
        
        # 直接映射的参数
        direct_mappings = {
            'name': 'name',
            'display_name': 'display_name',
            'entry': 'entry',
            'version': 'version',
            'publisher': 'publisher',
            'icon': 'icon',
            'license': 'license',
            'readme': 'readme',
            'hooks': 'hooks',
            'onefile': 'onefile',
            'skip_installer': 'skip_installer',
            'skip_exe': 'skip_exe',
            'inno_setup_path': 'inno_setup_path'
        }
        
        for arg_key, config_key in direct_mappings.items():
            if arg_key in args and args[arg_key] is not None:
                config[config_key] = args[arg_key]
        
        return config
    
    def _validate_config(self):
        """验证配置的有效性"""
        errors = []
        warnings = []
        
        # 检查必需字段
        required_fields = ['name', 'entry']
        for field in required_fields:
            if not self.merged_config.get(field):
                errors.append(f"缺少必需配置项: {field}")
        
        # 检查文件路径
        entry_file = self.merged_config.get('entry')
        if entry_file and not os.path.exists(entry_file):
            errors.append(f"入口文件不存在: {entry_file}")
        
        icon_file = self.merged_config.get('icon')
        if icon_file and not os.path.exists(icon_file):
            warnings.append(f"图标文件不存在: {icon_file}")
        
        # 检查重复配置
        duplicates = self._check_duplicate_configs()
        if duplicates:
            warnings.extend([f"配置重复: {dup}" for dup in duplicates])
        
        if errors:
            raise ValueError(f"配置验证失败: {'; '.join(errors)}")
        
        # 记录警告（这里可以通过日志系统输出）
        for warning in warnings:
            print(f"警告: {warning}")
    
    def _check_duplicate_configs(self) -> List[str]:
        """检查重复配置项"""
        duplicates = []
        
        if not self.raw_config:
            return duplicates
        
        # 获取全局配置的键
        global_keys = set(self.raw_config.keys()) - {'platform_specific', 'platforms'}
        
        # 检查平台配置中的重复项
        platform_config = self._get_platform_config()
        platform_keys = set(platform_config.keys())
        
        duplicate_keys = global_keys.intersection(platform_keys)
        duplicates.extend(duplicate_keys)
        
        return duplicates
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        keys = key.split('.')
        value = self.merged_config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_pyinstaller_config(self) -> Dict[str, Any]:
        """
        获取PyInstaller配置
        
        Returns:
            Dict[str, Any]: PyInstaller配置
        """
        config = {}
        
        # 从顶级配置中获取PyInstaller相关项
        pyinstaller_keys = [
            'onefile', 'windowed', 'console', 'icon', 'name',
            'distpath', 'workpath', 'specpath', 'debug', 'clean',
            'noconfirm', 'strip', 'noupx', 'optimize'
        ]
        
        for key in pyinstaller_keys:
            value = self.get(key)
            if value is not None:
                config[key] = value
        
        # 获取pyinstaller节中的配置
        pyinstaller_section = self.get('pyinstaller', {})
        config.update(pyinstaller_section)
        
        # 处理平台特定的PyInstaller配置
        platform_pyinstaller = self._get_platform_config().get('pyinstaller', {})
        config.update(platform_pyinstaller)
        
        # 添加 macOS 特定的配置
        if self.current_platform == 'macos':
            platform_config = self._get_platform_config()
            
            # Bundle Identifier
            if 'bundle_identifier' in platform_config:
                config['osx_bundle_identifier'] = platform_config['bundle_identifier']
        
        return config
    
    def get_platform_installer_config(self, installer_type: str) -> Dict[str, Any]:
        """
        获取平台特定安装器配置
        
        Args:
            installer_type: 安装器类型 (如 'inno_setup', 'create_dmg', 'deb')
            
        Returns:
            Dict[str, Any]: 安装器配置
        """
        platform_config = self._get_platform_config()
        return platform_config.get(installer_type, {})
    
    def get_app_info(self) -> Dict[str, Any]:
        """
        获取应用程序基本信息
        
        Returns:
            Dict[str, Any]: 应用信息字典
        """
        return {
            'name': self.get('name'),
            'display_name': self.get('display_name') or self.get('name'),
            'version': self.get('version'),
            'publisher': self.get('publisher'),
            'entry': self.get('entry'),
            'icon': self.get('icon'),
            'license': self.get('license'),
            'readme': self.get('readme')
        }
    
    def save_merged_config(self, output_path: str):
        """
        保存合并后的配置到文件
        
        Args:
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.merged_config, f, indent=2, ensure_ascii=False)