#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
macOS Entitlements.plist 自动生成器
根据配置自动生成 entitlements.plist 文件
"""

import os
from typing import Dict, Any, List, Set
from pathlib import Path


class EntitlementsGenerator:
    """macOS Entitlements.plist 自动生成器"""
    
    # Info.plist 权限描述到 Entitlements 权限的映射
    PRIVACY_TO_ENTITLEMENTS_MAPPING = {
        # 媒体设备权限
        'NSMicrophoneUsageDescription': [
            'com.apple.security.device.microphone',
            'com.apple.security.device.audio-input'
        ],
        'NSCameraUsageDescription': [
            'com.apple.security.device.camera'
        ],
        
        # 位置服务权限
        'NSLocationWhenInUseUsageDescription': [
            'com.apple.security.personal-information.location'
        ],
        'NSLocationAlwaysAndWhenInUseUsageDescription': [
            'com.apple.security.personal-information.location'
        ],
        
        # 个人信息权限
        'NSContactsUsageDescription': [
            'com.apple.security.personal-information.addressbook'
        ],
        'NSCalendarsUsageDescription': [
            'com.apple.security.personal-information.calendars'
        ],
        'NSRemindersUsageDescription': [
            'com.apple.security.personal-information.calendars'
        ],
        
        # 照片和媒体权限
        'NSPhotoLibraryUsageDescription': [
            'com.apple.security.assets.pictures.read-only'
        ],
        'NSPhotoLibraryAddUsageDescription': [
            'com.apple.security.assets.pictures.read-write'
        ],
        
        # 音乐权限
        'NSAppleMusicUsageDescription': [
            'com.apple.security.assets.music.read-only'
        ],
        
        # 蓝牙权限
        'NSBluetoothAlwaysUsageDescription': [
            'com.apple.security.device.bluetooth'
        ],
        'NSBluetoothPeripheralUsageDescription': [
            'com.apple.security.device.bluetooth'
        ],
        
        # 网络权限
        'NSLocalNetworkUsageDescription': [
            'com.apple.security.network.client',
            'com.apple.security.network.server'
        ],
    }
    
    # 配置键到 Info.plist 键的映射
    CONFIG_TO_PLIST_MAPPING = {
        'microphone_usage_description': 'NSMicrophoneUsageDescription',
        'camera_usage_description': 'NSCameraUsageDescription',
        'location_when_in_use_usage_description': 'NSLocationWhenInUseUsageDescription',
        'location_always_and_when_in_use_usage_description': 'NSLocationAlwaysAndWhenInUseUsageDescription',
        'contacts_usage_description': 'NSContactsUsageDescription',
        'calendars_usage_description': 'NSCalendarsUsageDescription',
        'reminders_usage_description': 'NSRemindersUsageDescription',
        'photo_library_usage_description': 'NSPhotoLibraryUsageDescription',
        'photo_library_add_usage_description': 'NSPhotoLibraryAddUsageDescription',
        'music_usage_description': 'NSAppleMusicUsageDescription',
        'bluetooth_always_usage_description': 'NSBluetoothAlwaysUsageDescription',
        'bluetooth_peripheral_usage_description': 'NSBluetoothPeripheralUsageDescription',
        'local_network_usage_description': 'NSLocalNetworkUsageDescription',
        'apple_events_usage_description': 'NSAppleEventsUsageDescription',
        'system_administration_usage_description': 'NSSystemAdministrationUsageDescription',
        'accessibility_usage_description': 'NSAccessibilityUsageDescription',
        'desktop_folder_usage_description': 'NSDesktopFolderUsageDescription',
        'documents_folder_usage_description': 'NSDocumentsFolderUsageDescription',
        'downloads_folder_usage_description': 'NSDownloadsFolderUsageDescription',
        'network_volumes_usage_description': 'NSNetworkVolumesUsageDescription',
        'removable_volumes_usage_description': 'NSRemovableVolumesUsageDescription',
    }
    
    def __init__(self):
        """初始化生成器"""
        pass
    
    def generate_entitlements(self, macos_config: Dict[str, Any], development: bool = False) -> str:
        """
        根据配置生成 entitlements.plist 内容
        
        Args:
            macos_config: macOS 配置字典
            development: 是否为开发版本
            
        Returns:
            str: entitlements.plist 文件内容
        """
        entitlements = {}
        
        # 根据隐私权限描述添加相应的 entitlements
        required_entitlements = self._extract_required_entitlements(macos_config)
        entitlements.update(required_entitlements)
        
        # 添加基础网络权限（大多数应用都需要）
        if self._needs_network_access(macos_config):
            entitlements['com.apple.security.network.client'] = True
            # 如果有网络服务需求，添加服务端权限
            if macos_config.get('local_network_usage_description'):
                entitlements['com.apple.security.network.server'] = True
        
        # 沙盒配置
        if macos_config.get('sandboxed', False):
            entitlements['com.apple.security.app-sandbox'] = True
            # 沙盒模式下的额外配置
            self._add_sandbox_entitlements(entitlements, macos_config)
        else:
            entitlements['com.apple.security.app-sandbox'] = False
        
        # 开发版本的特殊配置
        if development:
            self._add_development_entitlements(entitlements)
        
        # 特殊权限处理
        self._add_special_entitlements(entitlements, macos_config)
        
        return self._generate_plist_content(entitlements)
    
    def _extract_required_entitlements(self, macos_config: Dict[str, Any]) -> Dict[str, Any]:
        """从配置中提取所需的 entitlements"""
        entitlements = {}
        
        for config_key, description in macos_config.items():
            # 检查是否是权限描述配置
            if config_key in self.CONFIG_TO_PLIST_MAPPING and description:
                plist_key = self.CONFIG_TO_PLIST_MAPPING[config_key]
                
                # 获取对应的 entitlements
                if plist_key in self.PRIVACY_TO_ENTITLEMENTS_MAPPING:
                    for entitlement in self.PRIVACY_TO_ENTITLEMENTS_MAPPING[plist_key]:
                        if entitlement:  # 跳过空字符串
                            entitlements[entitlement] = True
        
        return entitlements
    
    def _needs_network_access(self, macos_config: Dict[str, Any]) -> bool:
        """判断应用是否需要网络访问权限"""
        # 如果配置了网络相关权限描述，说明需要网络访问
        network_indicators = [
            'local_network_usage_description',
        ]
        
        for indicator in network_indicators:
            if macos_config.get(indicator):
                return True
        
        # 如果配置了 ATS，说明需要网络访问
        if macos_config.get('app_transport_security'):
            return True
        
        # 默认假设需要网络访问（大多数现代应用都需要）
        return True
    
    def _add_sandbox_entitlements(self, entitlements: Dict[str, Any], macos_config: Dict[str, Any]):
        """添加沙盒模式下的 entitlements"""
        # 沙盒模式下需要明确指定文件访问权限
        if any(key in macos_config for key in [
            'desktop_folder_usage_description',
            'documents_folder_usage_description', 
            'downloads_folder_usage_description'
        ]):
            entitlements['com.apple.security.files.user-selected.read-write'] = True
        
        # 如果需要访问特定文件夹
        if macos_config.get('downloads_folder_usage_description'):
            entitlements['com.apple.security.files.downloads.read-write'] = True
        
        if macos_config.get('photo_library_usage_description'):
            entitlements['com.apple.security.assets.pictures.read-only'] = True
        
        if macos_config.get('photo_library_add_usage_description'):
            entitlements['com.apple.security.assets.pictures.read-write'] = True
    
    def _add_development_entitlements(self, entitlements: Dict[str, Any]):
        """添加开发版本的 entitlements（用于未签名应用）"""
        # 调试权限
        entitlements['com.apple.security.get-task-allow'] = True
        
        # Python 应用的必需权限
        entitlements['com.apple.security.cs.allow-jit'] = True
        entitlements['com.apple.security.cs.allow-unsigned-executable-memory'] = True
        
        # 禁用库验证（Python 动态加载需要）
        entitlements['com.apple.security.cs.disable-library-validation'] = True
        
        # 允许动态环境变量（Python 需要）
        entitlements['com.apple.security.cs.allow-dyld-environment-variables'] = True
        
        # 文件系统访问权限（未签名应用需要）
        entitlements['com.apple.security.files.user-selected.read-write'] = True
        entitlements['com.apple.security.files.documents.read-write'] = True
        entitlements['com.apple.security.files.downloads.read-write'] = True
        entitlements['com.apple.security.files.home.read-write'] = True
        
        # AppleScript 权限（自动化需要）
        entitlements['com.apple.security.automation.apple-events'] = True
    
    def _add_special_entitlements(self, entitlements: Dict[str, Any], macos_config: Dict[str, Any]):
        """添加特殊权限配置"""
        # AppleScript 权限需要特殊处理
        if macos_config.get('apple_events_usage_description'):
            # 添加常见的脚本目标
            scripting_targets = {
                'com.apple.finder': ['com.apple.events.appleevents'],
                'com.apple.systemevents': ['com.apple.events.appleevents']
            }
            
            # 如果用户自定义了脚本目标，使用用户配置
            if 'scripting_targets' in macos_config:
                scripting_targets.update(macos_config['scripting_targets'])
            
            entitlements['com.apple.security.scripting-targets'] = scripting_targets
        
        # 应用组权限
        if 'app_groups' in macos_config:
            app_groups = macos_config['app_groups']
            if isinstance(app_groups, list):
                entitlements['com.apple.security.application-groups'] = app_groups
        
        # 打印权限
        if macos_config.get('print_access', False):
            entitlements['com.apple.security.print'] = True
    
    def _generate_plist_content(self, entitlements: Dict[str, Any]) -> str:
        """生成 plist 文件内容"""
        content_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
            '<plist version="1.0">',
            '<dict>'
        ]
        
        # 按键名排序以确保输出一致性
        for key in sorted(entitlements.keys()):
            value = entitlements[key]
            content_parts.extend(self._format_plist_entry(key, value))
        
        content_parts.extend([
            '</dict>',
            '</plist>'
        ])
        
        return '\n'.join(content_parts)
    
    def _format_plist_entry(self, key: str, value: Any) -> List[str]:
        """格式化单个 plist 条目"""
        lines = [f'    <key>{key}</key>']
        
        if isinstance(value, bool):
            bool_str = "true" if value else "false"
            lines.append(f'    <{bool_str}/>')
        elif isinstance(value, str):
            lines.append(f'    <string>{value}</string>')
        elif isinstance(value, (int, float)):
            lines.append(f'    <real>{value}</real>')
        elif isinstance(value, list):
            lines.append('    <array>')
            for item in value:
                if isinstance(item, str):
                    lines.append(f'        <string>{item}</string>')
            lines.append('    </array>')
        elif isinstance(value, dict):
            lines.append('    <dict>')
            for sub_key in sorted(value.keys()):
                sub_value = value[sub_key]
                lines.append(f'        <key>{sub_key}</key>')
                if isinstance(sub_value, list):
                    lines.append('        <array>')
                    for item in sub_value:
                        lines.append(f'            <string>{item}</string>')
                    lines.append('        </array>')
                else:
                    lines.append(f'        <string>{sub_value}</string>')
            lines.append('    </dict>')
        
        return lines
    
    def generate_entitlements_file(self, 
                                 macos_config: Dict[str, Any], 
                                 output_path: Path,
                                 development: bool = False) -> bool:
        """
        生成 entitlements.plist 文件
        
        Args:
            macos_config: macOS 配置字典
            output_path: 输出文件路径
            development: 是否为开发版本
            
        Returns:
            bool: 是否生成成功
        """
        try:
            content = self.generate_entitlements(macos_config, development)
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"生成 entitlements.plist 失败: {e}")
            return False
    
    def get_required_entitlements_summary(self, macos_config: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        获取所需权限的摘要信息
        
        Args:
            macos_config: macOS 配置字典
            
        Returns:
            Dict: 权限分类摘要
        """
        summary = {
            '设备权限': [],
            '网络权限': [],
            '文件访问权限': [],
            '个人信息权限': [],
            '系统权限': [],
            '开发权限': []
        }
        
        # 分析配置中的权限
        for config_key, description in macos_config.items():
            if config_key in self.CONFIG_TO_PLIST_MAPPING and description:
                permission_name = self._get_permission_friendly_name(config_key)
                category = self._get_permission_category(config_key)
                
                if category in summary:
                    summary[category].append(permission_name)
        
        # 移除空的分类
        return {k: v for k, v in summary.items() if v}
    
    def _get_permission_friendly_name(self, config_key: str) -> str:
        """获取权限的友好名称"""
        name_mapping = {
            'microphone_usage_description': '麦克风访问',
            'camera_usage_description': '摄像头访问',
            'location_when_in_use_usage_description': '位置服务（使用时）',
            'location_always_and_when_in_use_usage_description': '位置服务（始终）',
            'contacts_usage_description': '通讯录访问',
            'calendars_usage_description': '日历访问',
            'reminders_usage_description': '提醒事项访问',
            'photo_library_usage_description': '照片库访问',
            'photo_library_add_usage_description': '照片库写入',
            'bluetooth_always_usage_description': '蓝牙访问',
            'local_network_usage_description': '本地网络访问',
            'apple_events_usage_description': 'AppleScript 控制',
            'system_administration_usage_description': '系统管理权限',
            'accessibility_usage_description': '辅助功能',
            'desktop_folder_usage_description': '桌面文件夹访问',
            'documents_folder_usage_description': '文档文件夹访问',
            'downloads_folder_usage_description': '下载文件夹访问',
        }
        return name_mapping.get(config_key, config_key)
    
    def _get_permission_category(self, config_key: str) -> str:
        """获取权限所属分类"""
        category_mapping = {
            'microphone_usage_description': '设备权限',
            'camera_usage_description': '设备权限',
            'bluetooth_always_usage_description': '设备权限',
            'bluetooth_peripheral_usage_description': '设备权限',
            
            'local_network_usage_description': '网络权限',
            
            'contacts_usage_description': '个人信息权限',
            'calendars_usage_description': '个人信息权限',
            'reminders_usage_description': '个人信息权限',
            'location_when_in_use_usage_description': '个人信息权限',
            'location_always_and_when_in_use_usage_description': '个人信息权限',
            
            'photo_library_usage_description': '文件访问权限',
            'photo_library_add_usage_description': '文件访问权限',
            'desktop_folder_usage_description': '文件访问权限',
            'documents_folder_usage_description': '文件访问权限',
            'downloads_folder_usage_description': '文件访问权限',
            
            'apple_events_usage_description': '系统权限',
            'system_administration_usage_description': '系统权限',
            'accessibility_usage_description': '系统权限',
        }
        return category_mapping.get(config_key, '其他权限')