#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyInstaller配置构建器
支持所有PyInstaller选项的配置化映射
"""

import os
import platform
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from ..utils.entitlements_generator import EntitlementsGenerator
from ..utils.icon_converter import IconConverter


class PyInstallerConfigBuilder:
    """PyInstaller配置构建器，支持所有选项"""
    
    # 完整的PyInstaller选项映射
    PYINSTALLER_OPTIONS = {
        # 基本选项
        'onefile': '--onefile',
        'onedir': '--onedir', 
        'windowed': '--windowed',
        'console': '--console',
        'name': '--name',
        'icon': '--icon',
        
        # 路径选项
        'distpath': '--distpath',
        'workpath': '--workpath',
        'specpath': '--specpath',
        
        # 包含/排除选项
        'add_data': '--add-data',
        'add_binary': '--add-binary',
        'hidden_import': '--hidden-import',
        'exclude_module': '--exclude-module',
        'additional_hooks_dir': '--additional-hooks-dir',
        'runtime_hook': '--runtime-hook',
        'collect_submodules': '--collect-submodules',
        'collect_data': '--collect-data',
        'collect_binaries': '--collect-binaries',
        'collect_all': '--collect-all',
        'copy_metadata': '--copy-metadata',
        'recursive_copy_metadata': '--recursive-copy-metadata',
        
        # 高级选项
        'splash': '--splash',
        'version_file': '--version-file',
        'manifest': '--manifest',
        'resource': '--resource',
        'uac_admin': '--uac-admin',
        'uac_uiaccess': '--uac-uiaccess',
        
        # 压缩和优化选项
        'upx_dir': '--upx-dir',
        'upx_exclude': '--upx-exclude',
        'noupx': '--noupx',
        'strip': '--strip',
        'debug': '--debug',
        'optimize': '--optimize',
        
        # 构建选项
        'clean': '--clean',
        'noconfirm': '--noconfirm',
        'ascii': '--ascii',
        'key': '--key',
        
        # 日志选项
        'log_level': '--log-level',
        'quiet': '--quiet',
        
        # 兼容性选项
        'osx_bundle_identifier': '--osx-bundle-identifier',
        'target_architecture': '--target-architecture',
        'codesign_identity': '--codesign-identity',
        'osx_entitlements_file': '--osx-entitlements-file'
    }
    
    # 布尔类型选项（不需要值）
    BOOLEAN_OPTIONS = {
        'onefile', 'onedir', 'windowed', 'console', 'clean', 'noconfirm',
        'debug', 'strip', 'noupx', 'ascii', 'uac_admin', 'uac_uiaccess',
        'quiet'
    }
    
    # 列表类型选项（可以多次指定）
    LIST_OPTIONS = {
        'add_data', 'add_binary', 'hidden_import', 'exclude_module',
        'additional_hooks_dir', 'runtime_hook', 'collect_submodules',
        'collect_data', 'collect_binaries', 'collect_all', 'copy_metadata',
        'recursive_copy_metadata', 'upx_exclude', 'resource'
    }
    
    def __init__(self, current_platform: Optional[str] = None):
        """
        初始化配置构建器
        
        Args:
            current_platform: 当前平台 (windows/macos/linux)
        """
        self.current_platform = current_platform or self._detect_platform()
        self.entitlements_generator = EntitlementsGenerator()
        self.icon_converter = IconConverter()
    
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
    
    def build_command(self, config: Dict[str, Any], entry_script: str) -> List[str]:
        """
        根据配置构建PyInstaller命令
        
        Args:
            config: PyInstaller配置字典
            entry_script: 入口脚本路径
            
        Returns:
            List[str]: PyInstaller命令参数列表
        """
        command = ['pyinstaller']
        
        # 处理每个配置项
        for config_key, value in config.items():
            if config_key not in self.PYINSTALLER_OPTIONS:
                continue
                
            option_flag = self.PYINSTALLER_OPTIONS[config_key]
            
            if config_key in self.BOOLEAN_OPTIONS:
                if value:
                    command.append(option_flag)
            elif config_key in self.LIST_OPTIONS:
                if isinstance(value, list):
                    for item in value:
                        processed_item = self._process_list_item(config_key, item)
                        if processed_item:
                            command.extend([option_flag, processed_item])
                elif isinstance(value, str):
                    processed_item = self._process_list_item(config_key, value)
                    if processed_item:
                        command.extend([option_flag, processed_item])
            else:
                if value is not None and str(value).strip():
                    command.extend([option_flag, str(value)])
        
        # 添加入口脚本
        command.append(entry_script)
        
        return command
    
    def _process_list_item(self, config_key: str, item: str) -> Optional[str]:
        """
        处理列表类型选项的单个项目
        
        Args:
            config_key: 配置键
            item: 列表项
            
        Returns:
            Optional[str]: 处理后的项目
        """
        if config_key in ['add_data', 'add_binary']:
            return self._handle_path_item(item)
        else:
            return item
    
    def _handle_path_item(self, path_item: str) -> str:
        """
        处理路径类型的配置项，自动处理平台特定的路径分隔符
        
        Args:
            path_item: 路径配置项 (格式: source:destination 或 source;destination)
            
        Returns:
            str: 处理后的路径项
        """
        # 确定正确的分隔符
        separator = ';' if self.current_platform == 'windows' else ':'
        
        # 如果包含分隔符，则处理路径
        if ':' in path_item or ';' in path_item:
            # 规范化分隔符
            if self.current_platform == 'windows':
                # Windows使用分号
                path_item = path_item.replace(':', ';')
            else:
                # Unix系统使用冒号
                path_item = path_item.replace(';', ':')
        
        return path_item
    
    def build_spec_file_content(self, config: Dict[str, Any], entry_script: str) -> str:
        """
        构建.spec文件内容
        
        Args:
            config: PyInstaller配置字典
            entry_script: 入口脚本路径
            
        Returns:
            str: .spec文件内容
        """
        app_name = config.get('name', Path(entry_script).stem)
        
        # 构建Analysis配置
        analysis_config = self._build_analysis_config(config, entry_script)
        
        # 构建PYZ配置
        pyz_config = "PYZ(a.pure, a.zipped_data, cipher=block_cipher)"
        
        # 构建EXE配置
        exe_config = self._build_exe_config(config, app_name)
        
        # 构建COLLECT配置（仅在onedir模式下）
        collect_config = ""
        bundle_config = ""
        if not config.get('onefile', False):
            collect_config = f"""
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip={str(config.get('strip', False))},
               upx={str(not config.get('noupx', False))},
               upx_exclude={repr(config.get('upx_exclude', []))},
               name='{app_name}')"""
            
            # 添加macOS Bundle配置
            if self.current_platform == 'macos':
                bundle_config = self._build_bundle_config(config, app_name)
        
        # 组装完整的.spec文件内容
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
# Generated by UnifyPy 2.0

block_cipher = None

{analysis_config}

pyz = {pyz_config}

{exe_config}
{collect_config}
{bundle_config}
"""
        
        return spec_content
    
    def _build_analysis_config(self, config: Dict[str, Any], entry_script: str) -> str:
        """构建Analysis部分配置"""
        # 基本配置
        pathex = config.get('pathex', [])
        binaries = self._format_tuples_list(config.get('add_binary', []))
        datas = self._format_tuples_list(config.get('add_data', []))
        hiddenimports = config.get('hidden_import', [])
        hookspath = config.get('additional_hooks_dir', [])
        hooksconfig = {}
        runtime_hooks = config.get('runtime_hook', [])
        excludes = config.get('exclude_module', [])
        
        return f"""a = Analysis(
    ['{entry_script}'],
    pathex={repr(pathex)},
    binaries={repr(binaries)},
    datas={repr(datas)},
    hiddenimports={repr(hiddenimports)},
    hookspath={repr(hookspath)},
    hooksconfig={repr(hooksconfig)},
    runtime_hooks={repr(runtime_hooks)},
    excludes={repr(excludes)},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive={str(config.get('noarchive', False))},
)"""
    
    def _build_exe_config(self, config: Dict[str, Any], app_name: str) -> str:
        """构建EXE部分配置"""
        console = not config.get('windowed', False)
        disable_windowed_traceback = False
        target_arch = config.get('target_architecture')
        codesign_identity = config.get('codesign_identity')
        entitlements_file = config.get('osx_entitlements_file')
        icon = config.get('icon')
        version = config.get('version_file')
        uac_admin = config.get('uac_admin', False)
        uac_uiaccess = config.get('uac_uiaccess', False)
        
        exe_config = f"""exe = EXE(
    pyz,
    a.scripts,"""
        
        if config.get('onefile', False):
            exe_config += """
    a.binaries,
    a.zipfiles,
    a.datas,"""
        
        exe_config += f"""
    [],
    name='{app_name}',
    debug={str(config.get('debug', False))},
    bootloader_ignore_signals=False,
    strip={str(config.get('strip', False))},
    upx={str(not config.get('noupx', False))},
    upx_exclude={repr(config.get('upx_exclude', []))},
    runtime_tmpdir=None,
    console={str(console)},
    disable_windowed_traceback={str(disable_windowed_traceback)},"""
        
        if target_arch:
            exe_config += f"""
    target_arch='{target_arch}',"""
            
        if codesign_identity:
            exe_config += f"""
    codesign_identity='{codesign_identity}',"""
            
        if entitlements_file:
            exe_config += f"""
    entitlements_file='{entitlements_file}',"""
            
        if icon:
            exe_config += f"""
    icon='{icon}',"""
            
        if version:
            exe_config += f"""
    version='{version}',"""
            
        if uac_admin:
            exe_config += f"""
    uac_admin={str(uac_admin)},"""
            
        if uac_uiaccess:
            exe_config += f"""
    uac_uiaccess={str(uac_uiaccess)},"""
        
        exe_config += """
)"""
        
        return exe_config
    
    def _format_tuples_list(self, items: List[str]) -> List[tuple]:
        """
        将路径字符串列表转换为元组列表
        
        Args:
            items: 路径字符串列表 (格式: "source:dest" 或 "source;dest")
            
        Returns:
            List[tuple]: 元组列表 [(source, dest), ...]
        """
        tuples_list = []
        for item in items:
            if isinstance(item, str):
                # 根据平台确定分隔符
                separator = ';' if self.current_platform == 'windows' else ':'
                if separator in item:
                    parts = item.split(separator, 1)
                    tuples_list.append((parts[0], parts[1]))
                else:
                    # 如果没有指定目标路径，使用源路径的文件名
                    tuples_list.append((item, os.path.basename(item)))
        
        return tuples_list
    
    def _build_bundle_config(self, config: Dict[str, Any], app_name: str) -> str:
        """构建macOS Bundle配置"""
        if self.current_platform != 'macos':
            return ""
        
        # 获取macOS平台配置
        # 支持两种配置结构: 直接的macos配置或platforms.macos配置
        macos_config = config.get('macos', {})
        if not macos_config and 'platforms' in config:
            macos_config = config.get('platforms', {}).get('macos', {})
        
        # Bundle标识符
        bundle_id = macos_config.get('bundle_identifier', f'com.example.{app_name.lower()}')
        
        # Info.plist配置
        info_plist = {
            'CFBundleName': app_name,
            'CFBundleDisplayName': app_name,
            'CFBundleExecutable': app_name,
            'CFBundlePackageType': 'APPL',
            'CFBundleVersion': config.get('version', '1.0.0'),
            'CFBundleShortVersionString': config.get('version', '1.0.0'),
            'CFBundleIdentifier': bundle_id,
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13.0',
            'LSApplicationCategoryType': 'public.app-category.productivity',
            'NSHumanReadableCopyright': f'Copyright © 2024 {config.get("publisher", "Unknown")}',
            'LSUIElement': False,
            'NSSupportsAutomaticGraphicsSwitching': True,
        }
        
        # 添加macOS特定配置
        if 'minimum_system_version' in macos_config:
            info_plist['LSMinimumSystemVersion'] = macos_config['minimum_system_version']
        
        if 'category' in macos_config:
            info_plist['LSApplicationCategoryType'] = macos_config['category']
        
        if 'copyright' in macos_config:
            info_plist['NSHumanReadableCopyright'] = macos_config['copyright']
        
        if 'high_resolution_capable' in macos_config:
            info_plist['NSHighResolutionCapable'] = macos_config['high_resolution_capable']
        
        if 'supports_automatic_graphics_switching' in macos_config:
            info_plist['NSSupportsAutomaticGraphicsSwitching'] = macos_config['supports_automatic_graphics_switching']
        
        if 'ui_element' in macos_config:
            info_plist['LSUIElement'] = macos_config['ui_element']
        
        # 添加完整的隐私权限描述配置
        privacy_permissions = {
            'microphone_usage_description': 'NSMicrophoneUsageDescription',
            'camera_usage_description': 'NSCameraUsageDescription',
            'location_when_in_use_usage_description': 'NSLocationWhenInUseUsageDescription',
            'location_always_and_when_in_use_usage_description': 'NSLocationAlwaysAndWhenInUseUsageDescription',
            'contacts_usage_description': 'NSContactsUsageDescription',
            'calendars_usage_description': 'NSCalendarsUsageDescription',
            'reminders_usage_description': 'NSRemindersUsageDescription',
            'photo_library_usage_description': 'NSPhotoLibraryUsageDescription',
            'photo_library_add_usage_description': 'NSPhotoLibraryAddUsageDescription',
            'motion_usage_description': 'NSMotionUsageDescription',
            'health_share_usage_description': 'NSHealthShareUsageDescription',
            'health_update_usage_description': 'NSHealthUpdateUsageDescription',
            'home_kit_usage_description': 'NSHomeKitUsageDescription',
            'siri_usage_description': 'NSSiriUsageDescription',
            'speech_recognition_usage_description': 'NSSpeechRecognitionUsageDescription',
            'tv_provider_usage_description': 'NSVideoSubscriberAccountUsageDescription',
            'music_usage_description': 'NSAppleMusicUsageDescription',
            'bluetooth_always_usage_description': 'NSBluetoothAlwaysUsageDescription',
            'bluetooth_peripheral_usage_description': 'NSBluetoothPeripheralUsageDescription',
        }
        
        for config_key, plist_key in privacy_permissions.items():
            if config_key in macos_config:
                info_plist[plist_key] = macos_config[config_key]
        
        # 系统访问权限
        system_permissions = {
            'apple_events_usage_description': 'NSAppleEventsUsageDescription',
            'system_administration_usage_description': 'NSSystemAdministrationUsageDescription',
            'accessibility_usage_description': 'NSAccessibilityUsageDescription',
        }
        
        for config_key, plist_key in system_permissions.items():
            if config_key in macos_config:
                info_plist[plist_key] = macos_config[config_key]
        
        # 文件夹访问权限
        folder_permissions = {
            'desktop_folder_usage_description': 'NSDesktopFolderUsageDescription',
            'documents_folder_usage_description': 'NSDocumentsFolderUsageDescription',
            'downloads_folder_usage_description': 'NSDownloadsFolderUsageDescription',
            'network_volumes_usage_description': 'NSNetworkVolumesUsageDescription',
            'removable_volumes_usage_description': 'NSRemovableVolumesUsageDescription',
        }
        
        for config_key, plist_key in folder_permissions.items():
            if config_key in macos_config:
                info_plist[plist_key] = macos_config[config_key]
        
        # 文件提供者权限
        if 'file_provider_presence_usage_description' in macos_config:
            info_plist['NSFileProviderPresenceUsageDescription'] = macos_config['file_provider_presence_usage_description']
        
        if 'file_provider_domain_usage_description' in macos_config:
            info_plist['NSFileProviderDomainUsageDescription'] = macos_config['file_provider_domain_usage_description']
        
        # 网络访问权限
        if 'local_network_usage_description' in macos_config:
            info_plist['NSLocalNetworkUsageDescription'] = macos_config['local_network_usage_description']
        
        # App Transport Security 配置
        if 'app_transport_security' in macos_config:
            ats_config = macos_config['app_transport_security']
            info_plist['NSAppTransportSecurity'] = ats_config
        
        # 沙盒配置
        if 'sandboxed' in macos_config and macos_config['sandboxed']:
            info_plist['com.apple.security.app-sandbox'] = True
        
        # 构建Bundle配置
        bundle_config = f"""
app = BUNDLE(
    coll,
    name='{app_name}.app',
    icon={repr(config.get('icon'))},
    bundle_identifier='{bundle_id}',
    info_plist={repr(info_plist)},
)"""
        
        return bundle_config
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """
        验证PyInstaller配置
        
        Args:
            config: 配置字典
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 检查互斥选项
        if config.get('onefile') and config.get('onedir'):
            errors.append("onefile 和 onedir 选项互斥")
        
        if config.get('windowed') and config.get('console'):
            errors.append("windowed 和 console 选项互斥")
        
        # 检查文件路径
        file_options = ['icon', 'version_file', 'manifest', 'splash', 'osx_entitlements_file']
        for option in file_options:
            file_path = config.get(option)
            if file_path and not os.path.exists(file_path):
                errors.append(f"{option} 指定的文件不存在: {file_path}")
        
        # 检查目录路径
        dir_options = ['distpath', 'workpath', 'specpath', 'upx_dir']
        for option in dir_options:
            dir_path = config.get(option)
            if dir_path and not os.path.isdir(dir_path):
                errors.append(f"{option} 指定的目录不存在: {dir_path}")
        
        # 验证 macOS 配置
        if self.current_platform == 'macos':
            errors.extend(self._validate_macos_config(config))
        
        return errors
    
    def _validate_macos_config(self, config: Dict[str, Any]) -> List[str]:
        """
        验证 macOS 特定配置
        
        Args:
            config: 配置字典
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 获取 macOS 配置
        macos_config = config.get('macos', {})
        if not macos_config and 'platforms' in config:
            macos_config = config.get('platforms', {}).get('macos', {})
        
        if not macos_config:
            return errors
        
        # 验证 Bundle Identifier 格式
        bundle_id = macos_config.get('bundle_identifier')
        if bundle_id:
            if not self._is_valid_bundle_identifier(bundle_id):
                errors.append(f"Bundle Identifier 格式无效: {bundle_id}")
        
        # 验证系统版本格式
        min_version = macos_config.get('minimum_system_version')
        if min_version and not self._is_valid_version(min_version):
            errors.append(f"系统最低版本格式无效: {min_version}")
        
        # 检查权限描述是否为空
        permission_keys = [
            'microphone_usage_description', 'camera_usage_description',
            'location_when_in_use_usage_description', 'location_always_and_when_in_use_usage_description',
            'contacts_usage_description', 'calendars_usage_description',
            'reminders_usage_description', 'photo_library_usage_description',
            'apple_events_usage_description', 'system_administration_usage_description',
            'accessibility_usage_description', 'desktop_folder_usage_description',
            'documents_folder_usage_description', 'downloads_folder_usage_description'
        ]
        
        for key in permission_keys:
            if key in macos_config:
                description = macos_config[key]
                if not description or not description.strip():
                    errors.append(f"macOS 权限描述不能为空: {key}")
                elif len(description.strip()) < 10:
                    errors.append(f"macOS 权限描述过短，建议提供更详细的说明: {key}")
        
        # 验证 App Transport Security 配置
        ats_config = macos_config.get('app_transport_security')
        if ats_config and isinstance(ats_config, dict):
            if 'NSAllowsArbitraryLoads' in ats_config and ats_config['NSAllowsArbitraryLoads']:
                errors.append("建议不要使用 NSAllowsArbitraryLoads，这会降低应用安全性")
        
        return errors
    
    def _is_valid_bundle_identifier(self, bundle_id: str) -> bool:
        """验证 Bundle Identifier 格式"""
        import re
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*$'
        return re.match(pattern, bundle_id) is not None
    
    def _is_valid_version(self, version: str) -> bool:
        """验证版本号格式"""
        import re
        pattern = r'^\d+(\.\d+)*$'
        return re.match(pattern, version) is not None
    
    def generate_entitlements_if_needed(self, config: Dict[str, Any], project_dir: Path, development: bool = False) -> Optional[str]:
        """
        根据配置自动生成 entitlements.plist 文件（如果需要）
        
        Args:
            config: 完整配置字典
            project_dir: 项目目录
            development: 是否为开发版本
            
        Returns:
            Optional[str]: 生成的 entitlements.plist 文件路径，如果不需要则返回 None
        """
        if self.current_platform != 'macos':
            return None
        
        # 获取 macOS 配置 - 优先从 platforms 结构中获取
        macos_config = {}
        if 'platforms' in config:
            macos_config = config.get('platforms', {}).get('macos', {})
        elif 'macos' in config:
            macos_config = config.get('macos', {})
        
        if not macos_config:
            return None
        
        # 优先检查项目中是否有现成的 entitlements.plist
        project_entitlements = project_dir / "entitlements.plist"
        if project_entitlements.exists():
            print(f"✅ 使用项目现有的 entitlements.plist: {project_entitlements}")
            return str(project_entitlements)
        
        # 检查是否已经指定了 entitlements 文件
        existing_entitlements = config.get('osx_entitlements_file')
        if not existing_entitlements:
            # 检查 pyinstaller 配置中是否指定了
            pyinstaller_config = config.get('pyinstaller', {})
            existing_entitlements = pyinstaller_config.get('osx_entitlements_file')
        
        # 如果已经有 entitlements 文件且存在，不自动生成
        if existing_entitlements and os.path.exists(existing_entitlements):
            print(f"✅ 使用配置中指定的 entitlements.plist: {existing_entitlements}")
            return existing_entitlements
        
        # 检查是否需要生成 entitlements
        if not self._needs_entitlements(macos_config):
            return None
        
        # 生成 entitlements 文件
        entitlements_path = project_dir / "auto_generated_entitlements.plist"
        
        success = self.entitlements_generator.generate_entitlements_file(
            macos_config, 
            entitlements_path,
            development
        )
        
        if success:
            print(f"✅ 自动生成 entitlements.plist: {entitlements_path}")
            
            # 显示权限摘要
            summary = self.entitlements_generator.get_required_entitlements_summary(macos_config)
            if summary:
                print("📋 检测到的权限需求:")
                for category, permissions in summary.items():
                    print(f"  {category}: {', '.join(permissions)}")
            
            return str(entitlements_path)
        else:
            print("❌ 自动生成 entitlements.plist 失败")
            return None
    
    def _needs_entitlements(self, macos_config: Dict[str, Any]) -> bool:
        """
        判断是否需要生成 entitlements.plist
        
        Args:
            macos_config: macOS 配置字典
            
        Returns:
            bool: 是否需要生成 entitlements
        """
        # 检查是否有任何权限描述
        permission_keys = [
            'microphone_usage_description', 'camera_usage_description',
            'location_when_in_use_usage_description', 'location_always_and_when_in_use_usage_description',
            'contacts_usage_description', 'calendars_usage_description',
            'reminders_usage_description', 'photo_library_usage_description',
            'photo_library_add_usage_description', 'bluetooth_always_usage_description',
            'bluetooth_peripheral_usage_description', 'local_network_usage_description',
            'apple_events_usage_description', 'system_administration_usage_description',
            'accessibility_usage_description', 'desktop_folder_usage_description',
            'documents_folder_usage_description', 'downloads_folder_usage_description'
        ]
        
        # 如果有任何权限描述，需要 entitlements
        for key in permission_keys:
            if macos_config.get(key):
                return True
        
        # 如果启用了沙盒模式，需要 entitlements
        if macos_config.get('sandboxed', False):
            return True
        
        # 如果有网络安全配置，可能需要 entitlements
        if macos_config.get('app_transport_security'):
            return True
        
        # 如果有应用组配置，需要 entitlements
        if macos_config.get('app_groups'):
            return True
        
        return False
    
    def update_config_with_auto_entitlements(self, config: Dict[str, Any], project_dir: Path, development: bool = False) -> Dict[str, Any]:
        """
        更新配置以包含自动生成的 entitlements
        
        Args:
            config: 原始配置字典
            project_dir: 项目目录
            development: 是否为开发版本
            
        Returns:
            Dict[str, Any]: 更新后的配置字典
        """
        updated_config = config.copy()
        
        # 生成 entitlements 文件
        entitlements_path = self.generate_entitlements_if_needed(config, project_dir, development)
        
        if entitlements_path:
            # 更新配置以使用生成的 entitlements 文件
            if 'pyinstaller' not in updated_config:
                updated_config['pyinstaller'] = {}
            
            updated_config['pyinstaller']['osx_entitlements_file'] = entitlements_path
        
        return updated_config
    
    def _process_icon_for_platform(self, config: Dict[str, Any], project_dir: Path) -> Dict[str, Any]:
        """
        根据当前平台处理图标格式
        
        Args:
            config: PyInstaller配置
            project_dir: 项目目录
            
        Returns:
            Dict[str, Any]: 处理后的配置
        """
        processed_config = config.copy()
        icon_path = config.get('icon')
        
        if not icon_path:
            return processed_config
        
        # 确定目标格式
        target_format = 'icns' if self.current_platform == 'macos' else 'ico' if self.current_platform == 'windows' else 'png'
        
        # 转换图标
        converted_icon = self.icon_converter.ensure_icon_format(icon_path, target_format, project_dir)
        
        if converted_icon:
            processed_config['icon'] = converted_icon
            print(f"🎨 图标已转换为 {target_format.upper()} 格式: {converted_icon}")
        else:
            print(f"⚠️ 图标转换失败，使用原始文件: {icon_path}")
        
        return processed_config