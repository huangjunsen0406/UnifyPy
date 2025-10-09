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

    def get_cached_file_path(self, platform: str, file_type: str, arch: str = None) -> Path:
        """获取缓存文件路径
        
        Args:
            platform: 平台名称 (windows, macos, linux)
            file_type: 文件类型 (iss, control, spec, plist, dmg_config, pkg_config)
            arch: 架构名称（可选，用于区分不同架构的配置）
            
        Returns:
            Path: 缓存文件路径
        """
        filename_map = {
            "windows": {
                "iss": "setup.iss",
            },
            "linux": {
                "control": "control",
                "spec": "app.spec",
                "desktop": "app.desktop",
            },
            "macos": {
                "plist": "Info.plist",
                "dmg_config": "dmg_config.json",
                "pkg_config": "pkg_config.json",
            }
        }
        
        filename = filename_map.get(platform, {}).get(file_type)
        if not filename:
            raise ValueError(f"不支持的平台/文件类型: {platform}/{file_type}")
        
        # 如果指定了架构，在文件名中包含架构信息
        if arch and platform in ["linux"]:  # Linux 可能需要区分不同架构
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            filename = f"{name}_{arch}.{ext}" if ext else f"{name}_{arch}"
        
        # 创建平台子目录
        platform_dir = self.cache_dir / platform
        platform_dir.mkdir(exist_ok=True)
        
        return platform_dir / filename

    def save_cached_file(self, platform: str, file_type: str, content: str):
        """保存缓存文件
        
        Args:
            platform: 平台名称
            file_type: 文件类型
            content: 文件内容
        """
        file_path = self.get_cached_file_path(platform, file_type)
        
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def load_cached_file(self, platform: str, file_type: str) -> Optional[str]:
        """加载缓存文件
        
        Args:
            platform: 平台名称
            file_type: 文件类型
            
        Returns:
            Optional[str]: 文件内容，如果不存在则返回 None
        """
        try:
            file_path = self.get_cached_file_path(platform, file_type)
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception:
            pass
        
        return None

    def clear_cache(self, platform: str = None):
        """清理缓存
        
        Args:
            platform: 平台名称（可选），如果指定则只清理该平台的缓存
        """
        if platform:
            # 清理特定平台的缓存
            metadata = self.load_metadata()
            if "platform_hashes" in metadata and platform in metadata["platform_hashes"]:
                del metadata["platform_hashes"][platform]
                self.save_metadata(metadata)
            
            # 删除对应的缓存文件
            for file_type in ["iss", "control", "spec", "plist"]:
                try:
                    file_path = self.get_cached_file_path(platform, file_type)
                    if file_path.exists():
                        file_path.unlink()
                except Exception:
                    pass
        else:
            # 清理所有缓存
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir()
            
            # 重置元数据
            metadata = self.load_metadata()
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

    def pre_generate_all_platform_configs(self, config: Dict[str, Any], config_file_path: str, progress_callback=None) -> Dict[str, bool]:
        """预生成所有平台的配置文件

        Args:
            config: 配置字典
            config_file_path: 配置文件路径
            progress_callback: 进度回调函数 callback(message, level='info')

        Returns:
            Dict[str, bool]: 各平台配置生成结果
        """
        results = {}

        def log(message, level='info'):
            """统一的日志输出"""
            if progress_callback:
                progress_callback(message, level)
            else:
                print(message)

        log("开始预生成多平台配置", 'info')

        # 确保 AppID 存在
        app_id = self.get_or_generate_app_id(config)
        config_app_id = config.get("platforms", {}).get("windows", {}).get("inno_setup", {}).get("app_id")

        # 只有在配置文件中没有 AppID 时才更新
        if not config_app_id and config_file_path:
            if self.update_build_config_with_app_id(config_file_path, app_id):
                log(f"AppID 已生成并写入配置: {app_id[:8]}...", 'success')
                # 重新加载配置
                import json
                try:
                    with open(config_file_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                except Exception as e:
                    log(f"重新加载配置失败: {e}", 'warning')
            else:
                log("AppID 写入配置文件失败", 'warning')
        elif config_app_id:
            log(f"使用现有 AppID: {config_app_id[:8]}...", 'info')

        # 生成各平台配置
        platform_generators = {
            "windows": self._generate_windows_configs,
            "macos": self._generate_macos_configs,
            "linux": self._generate_linux_configs,
        }

        for platform, generator in platform_generators.items():
            if platform in config.get("platforms", {}):
                try:
                    log(f"生成 {platform.upper()} 配置", 'info')
                    success = generator(config, platform)
                    results[platform] = success

                    if success:
                        # 保存平台配置哈希
                        platform_hash = self.calculate_config_hash(config, platform)
                        self.save_config_hash(platform_hash, platform)
                        log(f"{platform.upper()} 配置已生成", 'success')
                    else:
                        log(f"{platform.upper()} 配置生成失败", 'error')

                except Exception as e:
                    log(f"{platform.upper()} 配置生成错误: {e}", 'error')
                    results[platform] = False
            else:
                results[platform] = "skipped"

        # 保存全局配置哈希
        global_hash = self.calculate_config_hash(config)
        self.save_config_hash(global_hash)

        log("多平台配置预生成完成", 'success')
        return results

    def _generate_windows_configs(self, config: Dict[str, Any], platform: str) -> bool:
        """生成 Windows 平台配置
        
        Args:
            config: 配置字典
            platform: 平台名称
            
        Returns:
            bool: 生成是否成功
        """
        try:
            from unifypy.platforms.windows.inno_setup import InnoSetupPackager
            
            # 模拟生成 ISS 文件内容
            iss_content = self._build_windows_iss(config)
            
            # 保存 ISS 文件
            self.save_cached_file("windows", "iss", iss_content)
            
            return True
            
        except Exception as e:
            print(f"Windows 配置生成失败: {e}")
            return False

    def _generate_macos_configs(self, config: Dict[str, Any], platform: str) -> bool:
        """生成 macOS 平台配置
        
        Args:
            config: 配置字典
            platform: 平台名称
            
        Returns:
            bool: 生成是否成功
        """
        try:
            # 生成 Info.plist
            plist_content = self._build_macos_plist(config)
            self.save_cached_file("macos", "plist", plist_content)
            
            # 生成 DMG 配置
            dmg_config = self._build_dmg_config(config)
            import json
            dmg_config_str = json.dumps(dmg_config, indent=2, ensure_ascii=False)
            self.save_cached_file("macos", "dmg_config", dmg_config_str)
            
            return True
            
        except Exception as e:
            print(f"macOS 配置生成失败: {e}")
            return False

    def _generate_linux_configs(self, config: Dict[str, Any], platform: str) -> bool:
        """生成 Linux 平台配置
        
        Args:
            config: 配置字典
            platform: 平台名称
            
        Returns:
            bool: 生成是否成功
        """
        try:
            # 生成 DEB 控制文件
            if "deb" in config.get("platforms", {}).get("linux", {}):
                control_content = self._build_linux_control(config)
                self.save_cached_file("linux", "control", control_content)
            
            # 生成 RPM spec 文件
            if "rpm" in config.get("platforms", {}).get("linux", {}):
                spec_content = self._build_rpm_spec(config)
                self.save_cached_file("linux", "spec", spec_content)
            
            # 生成桌面文件
            desktop_content = self._build_desktop_file(config)
            self.save_cached_file("linux", "desktop", desktop_content)
            
            return True
            
        except Exception as e:
            print(f"Linux 配置生成失败: {e}")
            return False

    def _build_windows_iss(self, config: Dict[str, Any]) -> str:
        """构建 Windows ISS 文件内容"""
        app_name = config.get("name", "MyApp")
        version = config.get("version", "1.0.0")
        display_name = config.get("display_name", app_name)
        publisher = config.get("publisher", "Unknown Publisher")
        
        inno_config = config.get("platforms", {}).get("windows", {}).get("inno_setup", {})
        app_id = inno_config.get("app_id", "")
        
        iss_content = f"""[Setup]
AppId={{{app_id}}}
AppName={app_name}
AppVersion={version}
AppVerName={display_name} {version}
AppPublisher={publisher}
DefaultDirName={{autopf}}\\{app_name}
DefaultGroupName={app_name}
AllowNoIcons=yes
OutputDir=output
OutputBaseFilename={app_name}-{version}-setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
"""
        
        # 添加中文支持
        languages = inno_config.get("languages", [])
        if "chinesesimplified" in languages or "chinese" in languages:
            iss_content += 'Name: "chinesesimplified"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"\n'
        
        # 添加任务
        iss_content += "\n[Tasks]\n"
        if inno_config.get("create_desktop_icon", True):
            iss_content += 'Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked\n'
        
        # 添加文件
        iss_content += f"""
[Files]
Source: "dist\\{app_name}.exe"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\{display_name}"; Filename: "{{app}}\\{app_name}.exe"
"""
        
        if inno_config.get("create_desktop_icon", True):
            iss_content += f'Name: "{{autodesktop}}\\{display_name}"; Filename: "{{app}}\\{app_name}.exe"; Tasks: desktopicon\n'
        
        # 添加运行
        if inno_config.get("run_after_install", False):
            iss_content += f"""
[Run]
Filename: "{{app}}\\{app_name}.exe"; Description: "{{cm:LaunchProgram,{display_name}}}"; Flags: nowait postinstall skipifsilent
"""
        
        return iss_content

    def _build_macos_plist(self, config: Dict[str, Any]) -> str:
        """构建 macOS Info.plist 文件内容"""
        app_name = config.get("name", "MyApp")
        version = config.get("version", "1.0.0")
        display_name = config.get("display_name", app_name)
        
        macos_config = config.get("platforms", {}).get("macos", {})
        bundle_id = macos_config.get("bundle_identifier", f"com.example.{app_name.lower()}")
        
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDisplayName</key>
    <string>{display_name}</string>
    <key>CFBundleExecutable</key>
    <string>{app_name}</string>
    <key>CFBundleIconFile</key>
    <string>{app_name}.icns</string>
    <key>CFBundleIdentifier</key>
    <string>{bundle_id}</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>{app_name}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>{version}</string>
    <key>CFBundleVersion</key>
    <string>{version}</string>
    <key>LSMinimumSystemVersion</key>
    <string>{macos_config.get("minimum_system_version", "10.15.0")}</string>
    <key>NSHighResolutionCapable</key>
    <{str(macos_config.get("high_resolution_capable", True)).lower()}/>
    <key>NSSupportsAutomaticGraphicsSwitching</key>
    <{str(macos_config.get("supports_automatic_graphics_switching", True)).lower()}/>
</dict>
</plist>
"""
        return plist_content

    def _build_dmg_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """构建 DMG 配置"""
        app_name = config.get("name", "MyApp")
        display_name = config.get("display_name", app_name)
        
        dmg_config = config.get("platforms", {}).get("macos", {}).get("create_dmg", {})
        
        return {
            "volname": dmg_config.get("volname", f"{display_name} 安装器"),
            "window_size": dmg_config.get("window_size", [600, 400]),
            "window_pos": dmg_config.get("window_pos", [200, 120]),
            "icon_size": dmg_config.get("icon_size", 128),
            "icon_positions": dmg_config.get("icon", {
                f"{app_name}.app": [140, 200],
                "Applications": [460, 200]
            }),
            "format": dmg_config.get("format", "UDZO"),
            "filesystem": dmg_config.get("filesystem", "HFS+")
        }

    def _build_linux_control(self, config: Dict[str, Any]) -> str:
        """构建 Linux DEB 控制文件内容"""
        app_name = config.get("name", "MyApp").lower()
        version = config.get("version", "1.0.0")
        
        # 使用规范化架构映射
        from unifypy.core.environment import EnvironmentManager
        env_manager = EnvironmentManager(".")
        arch = env_manager.get_arch_for_format("deb")
        
        deb_config = config.get("platforms", {}).get("linux", {}).get("deb", {})
        
        control_content = f"""Package: {app_name}
Version: {version}
Section: {deb_config.get('section', 'utils')}
Priority: {deb_config.get('priority', 'optional')}
Architecture: {arch}
Maintainer: {deb_config.get('maintainer', config.get('publisher', 'Unknown <unknown@example.com>'))}
Description: {deb_config.get('description', config.get('display_name', app_name))}
"""
        
        # 添加依赖
        depends = deb_config.get("depends", [])
        if depends:
            if isinstance(depends, list):
                depends_str = ", ".join(depends)
            else:
                depends_str = str(depends)
            control_content += f"Depends: {depends_str}\n"
        
        return control_content

    def _build_rpm_spec(self, config: Dict[str, Any]) -> str:
        """构建 RPM spec 文件内容"""
        app_name = config.get("name", "MyApp")
        version = config.get("version", "1.0.0")
        
        # 使用规范化架构映射
        from unifypy.core.environment import EnvironmentManager
        env_manager = EnvironmentManager(".")
        arch = env_manager.get_arch_for_format("rpm")
        
        rpm_config = config.get("platforms", {}).get("linux", {}).get("rpm", {})
        
        spec_content = f"""Name:           {app_name.lower()}
Version:        {version}
Release:        1%{{?dist}}
Summary:        {rpm_config.get('summary', config.get('display_name', app_name))}

License:        {rpm_config.get('license', 'Unknown')}
URL:            {rpm_config.get('url', '')}
Source0:        %{{name}}-%{{version}}.tar.gz

BuildArch:      {arch}

%description
{rpm_config.get('description', config.get('display_name', app_name))}

%prep
%setup -q

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/opt/{app_name}
mkdir -p $RPM_BUILD_ROOT/usr/local/bin

# 复制应用文件
cp -r * $RPM_BUILD_ROOT/opt/{app_name}/

# 创建启动脚本
cat > $RPM_BUILD_ROOT/usr/local/bin/{app_name.lower()} << 'EOF'
#!/bin/bash
cd /opt/{app_name}
exec ./{app_name} "$@"
EOF
chmod +x $RPM_BUILD_ROOT/usr/local/bin/{app_name.lower()}

%files
%defattr(-,root,root,-)
/opt/{app_name}/*
/usr/local/bin/{app_name.lower()}

%changelog
* {self._get_current_date()} {rpm_config.get('packager', 'Unknown <unknown@example.com>')} - {version}-1
- Initial package
"""
        return spec_content

    def _build_desktop_file(self, config: Dict[str, Any]) -> str:
        """构建 Linux 桌面文件内容"""
        app_name = config.get("name", "MyApp")
        display_name = config.get("display_name", app_name)
        
        desktop_content = f"""[Desktop Entry]
Type=Application
Name={display_name}
Exec={app_name.lower()}
Icon={app_name.lower()}
Comment={config.get('description', display_name)}
Categories=Utility;Development;
Terminal=false
Version={config.get('version', '1.0.0')}
"""
        return desktop_content

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
