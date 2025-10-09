#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理系统 处理配置文件加载、合并和验证.
"""

import json
import os
from .platforms import normalize_platform
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConfigManager:
    """
    配置管理器，处理配置合并和验证.
    """

    def __init__(self, config_path: Optional[str] = None, args: Optional[Dict] = None):
        """初始化配置管理器.

        Args:
            config_path: 配置文件路径
            args: 命令行参数字典
        """
        self.config_path = config_path
        self.args = args or {}
        self.raw_config = {}
        self.merged_config = {}
        self.current_platform = self._detect_platform()
        
        # 获取项目目录用于路径解析
        if "project_dir" in self.args:
            self.project_dir = Path(self.args["project_dir"]).resolve()
        else:
            self.project_dir = Path.cwd()

        if config_path:
            self.raw_config = self._load_config(config_path)

        self.merged_config = self._merge_all_configs()
        self._validate_config()
    
    def resolve_path(self, path: str) -> Path:
        """
        解析配置中的路径，相对路径相对于项目目录.

        Args:
            path: 配置中的路径

        Returns:
            Path: 解析后的绝对路径
        """
        if not path:
            return Path()

        if os.path.isabs(path):
            return Path(path)
        else:
            return self.project_dir / path

    def preprocess_paths(self, config: dict) -> dict:
        """
        预处理配置中的文件路径，将相对路径转换为绝对路径.

        Args:
            config: 原始配置字典

        Returns:
            dict: 处理后的配置字典（深拷贝）
        """
        import copy
        processed_config = copy.deepcopy(config)

        # 需要处理的文件路径字段
        path_fields = [
            "icon", "license", "readme", "entry",
            "setup_icon", "license_file", "readme_file",
            "volicon", "version_file", "manifest"
        ]

        # 需要处理的数组路径字段
        array_path_fields = ["add_data", "add_binary", "datas", "binaries"]

        # 处理顶级路径字段
        for field in path_fields:
            if field in processed_config and processed_config[field]:
                path = processed_config[field]
                if not os.path.isabs(path):
                    processed_config[field] = str(self.project_dir / path)

        # 处理数组路径字段
        self._process_array_paths(processed_config, array_path_fields)

        # 处理嵌套配置中的路径（如平台特定配置）
        for platform_key in ["windows", "macos", "linux", "platforms"]:
            if platform_key in processed_config:
                platform_config = processed_config[platform_key]
                if isinstance(platform_config, dict):
                    self._process_nested_paths(platform_config, path_fields, array_path_fields)

        # 处理 PyInstaller 配置中的路径
        if "pyinstaller" in processed_config:
            pyinstaller_config = processed_config["pyinstaller"]
            if isinstance(pyinstaller_config, dict):
                self._process_nested_paths(pyinstaller_config, path_fields, array_path_fields)

        return processed_config

    def _process_array_paths(self, config: dict, array_path_fields: List[str]):
        """
        处理数组路径字段.

        Args:
            config: 配置字典
            array_path_fields: 数组路径字段列表
        """
        for field in array_path_fields:
            if field in config and config[field]:
                processed_list = []
                for item in config[field]:
                    if isinstance(item, str):
                        processed_item = self._process_path_item(item)
                        processed_list.append(processed_item)
                    else:
                        processed_list.append(item)
                config[field] = processed_list

    def _process_path_item(self, item: str) -> str:
        """
        处理单个路径项（可能包含 source:dest 格式）.

        Args:
            item: 路径项字符串

        Returns:
            str: 处理后的路径项
        """
        # 处理 "source:dest" 格式
        if ":" in item or ";" in item:
            separator = ":" if ":" in item else ";"
            parts = item.split(separator, 1)
            if len(parts) == 2:
                source, dest = parts
                if not os.path.isabs(source):
                    source = str(self.project_dir / source)
                return f"{source}{separator}{dest}"
            else:
                return item
        else:
            # 单个路径
            if not os.path.isabs(item):
                return str(self.project_dir / item)
            return item

    def _process_nested_paths(
        self,
        config: dict,
        path_fields: List[str],
        array_path_fields: List[str]
    ):
        """
        递归处理嵌套配置中的文件路径.

        Args:
            config: 配置字典
            path_fields: 单个路径字段列表
            array_path_fields: 数组路径字段列表
        """
        # 处理单个路径字段
        for field in path_fields:
            if field in config and config[field]:
                path = config[field]
                if isinstance(path, str) and not os.path.isabs(path):
                    config[field] = str(self.project_dir / path)

        # 处理数组路径字段
        self._process_array_paths(config, array_path_fields)

        # 递归处理嵌套字典
        for value in config.values():
            if isinstance(value, dict):
                self._process_nested_paths(value, path_fields, array_path_fields)

    def _detect_platform(self) -> str:
        """
        检测当前平台.
        """
        return normalize_platform()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载JSON配置文件.

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
            with open(config_path, "r", encoding="utf-8-sig") as f:
                config = json.load(f)
                return config
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"配置文件格式错误: {e}", e.doc, e.pos)
        except Exception as e:
            raise Exception(f"加载配置文件失败: {e}")

    def _merge_all_configs(self) -> Dict[str, Any]:
        """合并所有配置源 优先级: 命令行参数 > 平台特定配置 > 全局配置 > 默认配置.

        Returns:
            Dict[str, Any]: 合并后的配置
        """
        # 默认配置
        default_config = self._get_default_config()

        # 从原始配置开始
        merged = default_config.copy()

        # 合并文件配置的全局部分
        if self.raw_config:
            global_config = {
                k: v
                for k, v in self.raw_config.items()
                if k not in ["platform_specific", "platforms"]
            }
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
        """
        获取默认配置.
        """
        return {
            "name": "UnknownApp",
            "version": "1.0.0",
            "entry": "main.py",
            "publisher": "Unknown Publisher",
            "onefile": False,
            "skip_installer": False,
            "pyinstaller": {"clean": True, "noconfirm": True},
        }

    def _get_platform_config(self) -> Dict[str, Any]:
        """获取当前平台的特定配置.

        Returns:
            Dict[str, Any]: 平台特定配置
        """
        if not self.raw_config:
            return {}

        # 尝试新格式 (platforms)
        platforms = self.raw_config.get("platforms", {})
        if self.current_platform in platforms:
            return platforms[self.current_platform]

        # 尝试旧格式 (platform_specific)
        platform_specific = self.raw_config.get("platform_specific", {})
        if self.current_platform in platform_specific:
            return platform_specific[self.current_platform]

        return {}

    def _args_to_config(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """将命令行参数转换为配置格式.

        Args:
            args: 命令行参数字典

        Returns:
            Dict[str, Any]: 配置字典
        """
        config = {}

        # 直接映射的参数
        direct_mappings = {
            "name": "name",
            "display_name": "display_name",
            "entry": "entry",
            "version": "version",
            "publisher": "publisher",
            "icon": "icon",
            "license": "license",
            "readme": "readme",
            "hooks": "hooks",
            "onefile": "onefile",
            "skip_installer": "skip_installer",
            "skip_exe": "skip_exe",
            "inno_setup_path": "inno_setup_path",
        }

        for arg_key, config_key in direct_mappings.items():
            if arg_key in args and args[arg_key] is not None:
                config[config_key] = args[arg_key]

        return config

    def _validate_config(self):
        """
        验证配置的有效性.
        """
        errors = []
        warnings = []

        # 检查必需字段
        required_fields = ["name", "entry"]
        for field in required_fields:
            if not self.merged_config.get(field):
                errors.append(f"缺少必需配置项: {field}")

        # 检查文件路径
        entry_file = self.merged_config.get("entry")
        if entry_file:
            entry_full_path = self.resolve_path(entry_file)
            if not entry_full_path.exists():
                errors.append(f"入口文件不存在: {entry_file}")

        icon_file = self.merged_config.get("icon")
        if icon_file:
            icon_full_path = self.resolve_path(icon_file)
            if not icon_full_path.exists():
                warnings.append(f"图标文件不存在: {icon_file}")
        
        # 检查其他可能的文件路径
        file_fields = ["license", "readme"]
        for field in file_fields:
            file_path = self.merged_config.get(field)
            if file_path:
                full_path = self.resolve_path(file_path)
                if not full_path.exists():
                    warnings.append(f"{field}文件不存在: {file_path}")

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
        """
        检查重复配置项.
        """
        duplicates = []

        if not self.raw_config:
            return duplicates

        # 获取全局配置的键
        global_keys = set(self.raw_config.keys()) - {"platform_specific", "platforms"}

        # 检查平台配置中的重复项
        platform_config = self._get_platform_config()
        platform_keys = set(platform_config.keys())

        duplicate_keys = global_keys.intersection(platform_keys)
        duplicates.extend(duplicate_keys)

        return duplicates

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值.

        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值

        Returns:
            Any: 配置值
        """
        keys = key.split(".")
        value = self.merged_config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_pyinstaller_config(self) -> Dict[str, Any]:
        """获取PyInstaller配置.

        Returns:
            Dict[str, Any]: PyInstaller配置
        """
        config = {}

        # 从顶级配置中获取PyInstaller相关项
        pyinstaller_keys = [
            "onefile",
            "windowed",
            "console",
            "icon",
            "name",
            "distpath",
            "workpath",
            "specpath",
            "debug",
            "clean",
            "noconfirm",
            "strip",
            "noupx",
            "optimize",
        ]

        for key in pyinstaller_keys:
            value = self.get(key)
            if value is not None:
                config[key] = value

        # 获取pyinstaller节中的配置
        pyinstaller_section = self.get("pyinstaller", {})
        config.update(pyinstaller_section)

        # 处理平台特定的PyInstaller配置
        platform_pyinstaller = self._get_platform_config().get("pyinstaller", {})
        config.update(platform_pyinstaller)

        # 添加 macOS 特定的配置
        if self.current_platform == "macos":
            platform_config = self._get_platform_config()

            # Bundle Identifier
            if "bundle_identifier" in platform_config:
                config["osx_bundle_identifier"] = platform_config["bundle_identifier"]

        return config

    def get_platform_installer_config(self, installer_type: str) -> Dict[str, Any]:
        """获取平台特定安装器配置.

        Args:
            installer_type: 安装器类型 (如 'inno_setup', 'create_dmg', 'deb')

        Returns:
            Dict[str, Any]: 安装器配置
        """
        platform_config = self._get_platform_config()
        return platform_config.get(installer_type, {})

    def get_app_info(self) -> Dict[str, Any]:
        """获取应用程序基本信息.

        Returns:
            Dict[str, Any]: 应用信息字典
        """
        return {
            "name": self.get("name"),
            "display_name": self.get("display_name") or self.get("name"),
            "version": self.get("version"),
            "publisher": self.get("publisher"),
            "entry": self.get("entry"),
            "icon": self.get("icon"),
            "license": self.get("license"),
            "readme": self.get("readme"),
        }

    def save_merged_config(self, output_path: str):
        """保存合并后的配置到文件.

        Args:
            output_path: 输出文件路径
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.merged_config, f, indent=2, ensure_ascii=False)
