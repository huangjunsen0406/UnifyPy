#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能缓存管理器
支持配置文件 hash 对比和智能更新机制
"""

import os
import json
import hashlib
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, List
import uuid


class CacheManager:
    """
    智能缓存管理器
    
    负责管理 .unifypy/ 目录下的缓存文件和元数据
    支持配置变更检测和智能更新
    """

    def __init__(self, project_dir: str):
        """初始化缓存管理器
        
        Args:
            project_dir: 项目根目录
        """
        self.project_dir = Path(project_dir).resolve()
        self.unifypy_dir = self.project_dir / ".unifypy"
        self.cache_dir = self.unifypy_dir / "cache"
        self.metadata_file = self.unifypy_dir / "metadata.json"
        
        # 确保目录存在
        self._ensure_directories()

    def _ensure_directories(self):
        """确保缓存目录存在"""
        self.unifypy_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        
        # 创建 .gitignore 文件（仅忽略日志）
        gitignore_path = self.unifypy_dir / ".gitignore"
        if not gitignore_path.exists():
            with open(gitignore_path, "w") as f:
                f.write("# UnifyPy 缓存目录\n")
                f.write("# 大部分文件应该加入版本控制以支持 CI/CD\n\n")
                f.write("# 仅忽略日志文件\n")
                f.write("logs/\n")
                f.write("*.log\n")

    def calculate_config_hash(self, config: Dict[str, Any], platform: str = None) -> str:
        """计算配置文件的哈希值
        
        Args:
            config: 配置字典
            platform: 平台名称（可选，用于平台特定哈希）
            
        Returns:
            str: 配置的 SHA256 哈希值
        """
        # 过滤配置，排除动态参数
        filtered_config = self._filter_config_for_hash(config)
        
        # 构建哈希因子
        hash_factors = {
            "unifypy_version": "2.0.0",  # TODO: 从版本文件读取
            "build_config": filtered_config,
        }
        
        # 如果指定了平台，只计算平台相关配置
        if platform:
            platform_config = config.get("platforms", {}).get(platform, {})
            hash_factors["platform_config"] = platform_config
            hash_factors["platform"] = platform
        
        # 添加资源文件哈希
        resource_files = self._get_resource_files(config, platform)
        if resource_files:
            hash_factors["resource_files"] = resource_files

        # 模板文件（如存在）也纳入哈希，确保模板变更触发重生
        template_paths = [
            self.project_dir / "unifypy" / "templates" / "setup.iss.template",
            self.project_dir / "unifypy" / "templates" / "ChineseSimplified.isl.template",
        ]
        template_meta = {}
        for p in template_paths:
            try:
                if p.exists():
                    stat = p.stat()
                    template_meta[str(p)] = {"mtime": stat.st_mtime, "size": stat.st_size}
            except Exception:
                pass
        if template_meta:
            hash_factors["templates"] = template_meta
        
        # 计算 SHA256
        content = json.dumps(hash_factors, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def _get_resource_files(self, config: Dict[str, Any], platform: str = None) -> Dict[str, str]:
        """获取资源文件的哈希值
        
        Args:
            config: 配置字典
            platform: 平台名称
            
        Returns:
            Dict[str, str]: 文件路径到哈希值的映射
        """
        resource_hashes = {}
        
        # 全局资源文件
        global_resources = [
            config.get("icon"),
            config.get("license"),
        ]
        
        # 平台特定资源文件
        platform_resources = []
        if platform and platform in config.get("platforms", {}):
            platform_config = config["platforms"][platform]
            
            if platform == "windows":
                inno_setup = platform_config.get("inno_setup", {})
                platform_resources.extend([
                    inno_setup.get("setup_icon"),
                    inno_setup.get("license_file"),
                ])
            elif platform == "macos":
                platform_resources.extend([
                    platform_config.get("icon"),
                    platform_config.get("info_plist"),
                ])
            elif platform == "linux":
                for fmt in ["deb", "rpm"]:
                    fmt_config = platform_config.get(fmt, {})
                    platform_resources.append(fmt_config.get("icon"))
        
        # 计算存在文件的哈希
        all_resources = global_resources + platform_resources
        for resource_path in all_resources:
            if resource_path and os.path.exists(resource_path):
                try:
                    file_hash = self._calculate_file_hash(resource_path)
                    resource_hashes[resource_path] = file_hash
                except Exception:
                    # 文件读取失败，忽略
                    pass
        
        return resource_hashes

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件的 MD5 哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件的 MD5 哈希值
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def load_cached_hash(self, platform: str = None) -> Optional[str]:
        """加载缓存的配置哈希值

        Args:
            platform: 平台名称（可选）

        Returns:
            Optional[str]: 缓存的哈希值，如果不存在则返回 None
        """
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                if platform:
                    return metadata.get("platform_hashes", {}).get(platform)
                else:
                    return metadata.get("config_hash")
        except Exception:
            pass

        return None

    def save_config_hash(self, config_hash: str, platform: str = None):
        """保存配置哈希值到元数据文件
        
        Args:
            config_hash: 配置哈希值
            platform: 平台名称（可选）
        """
        # 加载现有元数据
        metadata = self.load_metadata()
        
        if platform:
            if "platform_hashes" not in metadata:
                metadata["platform_hashes"] = {}
            metadata["platform_hashes"][platform] = config_hash
        else:
            metadata["config_hash"] = config_hash
        
        # 更新时间戳
        import datetime
        metadata["last_updated"] = datetime.datetime.now().isoformat()
        
        # 保存元数据
        self.save_metadata(metadata)

    def load_metadata(self) -> Dict[str, Any]:
        """加载元数据文件
        
        Returns:
            Dict[str, Any]: 元数据字典
        """
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # 返回默认元数据
        return {
            "version": "2.0.0",
            "created": None,
            "app_id": None,
            "config_hash": None,
            "platform_hashes": {}
        }

    def save_metadata(self, metadata: Dict[str, Any]):
        """保存元数据文件
        
        Args:
            metadata: 元数据字典
        """
        # 确保目录存在
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def should_regenerate_config(self, config: Dict[str, Any], platform: str = None) -> bool:
        """检查是否需要重新生成配置文件
        
        Args:
            config: 当前配置
            platform: 平台名称（可选）
            
        Returns:
            bool: 是否需要重新生成
        """
        current_hash = self.calculate_config_hash(config, platform)
        cached_hash = self.load_cached_hash(platform)
        
        # 如果哈希不同或缓存不存在，需要重新生成
        return current_hash != cached_hash

    def get_or_generate_app_id(self, config: Dict[str, Any]) -> str:
        """获取或生成应用 ID
        
        Args:
            config: 配置字典
            
        Returns:
            str: 应用 ID
        """
        # 优先从配置文件读取
        app_id = config.get("platforms", {}).get("windows", {}).get("inno_setup", {}).get("app_id")
        
        if app_id:
            # 确保元数据中也有记录
            metadata = self.load_metadata()
            if metadata.get("app_id") != app_id:
                metadata["app_id"] = app_id
                self.save_metadata(metadata)
            return app_id
        
        # 从元数据中读取
        metadata = self.load_metadata()
        if metadata.get("app_id"):
            return metadata["app_id"]
        
        # 生成新的 AppID
        app_name = config.get("name", "MyApp")
        app_id = self._generate_app_id(app_name)
        
        # 保存到元数据
        metadata["app_id"] = app_id
        if not metadata.get("created"):
            import datetime
            metadata["created"] = datetime.datetime.now().isoformat()
        self.save_metadata(metadata)
        
        return app_id

    def _generate_app_id(self, app_name: str) -> str:
        """生成应用 ID
        
        Args:
            app_name: 应用名称
            
        Returns:
            str: 生成的应用 ID（无花括号格式）
        """
        # 基于应用名称生成确定性的 UUID
        namespace = uuid.NAMESPACE_DNS
        app_uuid = uuid.uuid5(namespace, app_name)
        
        # 返回无花括号的格式，因为 ISS 模板中会添加花括号
        return str(app_uuid).upper()

    def update_build_config_with_app_id(self, config_file_path: str, app_id: str) -> bool:
        """将生成的 AppID 写入构建配置文件
        
        Args:
            config_file_path: 配置文件路径
            app_id: 应用 ID
            
        Returns:
            bool: 是否成功更新
        """
        try:
            # 读取配置文件
            with open(config_file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 确保结构存在
            if "platforms" not in config:
                config["platforms"] = {}
            if "windows" not in config["platforms"]:
                config["platforms"]["windows"] = {}
            if "inno_setup" not in config["platforms"]["windows"]:
                config["platforms"]["windows"]["inno_setup"] = {}
            
            # 设置 AppID
            config["platforms"]["windows"]["inno_setup"]["app_id"] = app_id
            
            # 写回配置文件
            with open(config_file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"更新配置文件失败: {e}")
            return False

    def clear_cache(self, platform: str = None):
        """清理缓存（重置配置 hash）

        Args:
            platform: 平台名称（可选），如果指定则只清理该平台的 hash
        """
        metadata = self.load_metadata()

        if platform:
            # 清理特定平台的 hash
            if "platform_hashes" in metadata and platform in metadata["platform_hashes"]:
                del metadata["platform_hashes"][platform]
        else:
            # 清理所有 hash
            metadata["config_hash"] = None
            metadata["platform_hashes"] = {}

        self.save_metadata(metadata)

    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息
        
        Returns:
            Dict[str, Any]: 缓存状态信息
        """
        metadata = self.load_metadata()
        
        # 统计缓存文件
        cached_files = []
        total_size = 0
        
        if self.cache_dir.exists():
            for file_path in self.cache_dir.rglob("*"):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    cached_files.append({
                        "path": str(file_path.relative_to(self.cache_dir)),
                        "size": size,
                        "size_mb": round(size / 1024 / 1024, 2)
                    })
                    total_size += size
        
        return {
            "metadata": metadata,
            "cache_directory": str(self.cache_dir),
            "cached_files": cached_files,
            "total_files": len(cached_files),
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "unifypy_directory_exists": self.unifypy_dir.exists(),
            "metadata_file_exists": self.metadata_file.exists(),
        }

    def should_pre_generate_all_configs(self, config: Dict[str, Any]) -> bool:
        """检查是否需要预生成所有平台配置
        
        Args:
            config: 配置字典
            
        Returns:
            bool: 是否需要预生成
        """
        # 检查是否有任何平台配置发生变化
        all_platforms = ["windows", "macos", "linux"]
        
        for platform in all_platforms:
            if platform in config.get("platforms", {}):
                if self.should_regenerate_config(config, platform):
                    return True
        
        # 检查全局配置变化
        current_global_hash = self.calculate_config_hash(config)
        cached_global_hash = self.load_cached_hash()
        
        return current_global_hash != cached_global_hash

    def _get_current_date(self) -> str:
        """获取当前日期（RPM格式）"""
        import datetime
        import locale

        try:
            locale.setlocale(locale.LC_TIME, "C")
        except:
            pass

        return datetime.datetime.now().strftime("%a %b %d %Y")

    def _filter_config_for_hash(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """过滤配置，排除不影响缓存的动态参数
        
        Args:
            config: 原始配置字典
            
        Returns:
            Dict[str, Any]: 过滤后的配置字典
        """
        import copy
        filtered_config = copy.deepcopy(config)
        
        # 排除的动态参数
        exclude_keys = [
            "project_dir",  # 项目目录路径
            "temp_dir",     # 临时目录
            "dist_dir",     # 输出目录
            "installer_dir", # 安装程序目录
            "verbose",      # 详细输出模式
            "quiet",        # 静默模式
            "clean",        # 清理选项
            "skip_exe",     # 跳过可执行文件
            "skip_installer", # 跳过安装包
            "parallel",     # 并行构建
            "max_workers",  # 最大工作线程
            "no_rollback",  # 禁用回滚
        ]
        
        # 从顶级配置中移除动态参数
        for key in exclude_keys:
            filtered_config.pop(key, None)
        
        return filtered_config
