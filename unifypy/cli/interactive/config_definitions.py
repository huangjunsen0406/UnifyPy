#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置定义
定义所有可配置的选项和默认值
"""

from typing import Dict, Any


# macOS 权限定义（通用化描述）
MACOS_PERMISSIONS: Dict[str, Dict[str, str]] = {
    'microphone': {
        'key': 'NSMicrophoneUsageDescription',
        'label': 'Microphone (麦克风)',
        'hint': '录音、语音识别',
        'default_description': '此应用需要访问麦克风以实现录音功能'
    },
    'camera': {
        'key': 'NSCameraUsageDescription',
        'label': 'Camera (摄像头)',
        'hint': '拍照、视频通话',
        'default_description': '此应用需要访问摄像头以实现拍照或视频功能'
    },
    'speech_recognition': {
        'key': 'NSSpeechRecognitionUsageDescription',
        'label': 'Speech Recognition (语音识别)',
        'hint': '语音转文字',
        'default_description': '此应用需要使用语音识别功能以理解语音指令'
    },
    'local_network': {
        'key': 'NSLocalNetworkUsageDescription',
        'label': 'Local Network (本地网络)',
        'hint': '局域网访问',
        'default_description': '此应用需要访问本地网络以发现和连接设备'
    },
    'audio': {
        'key': 'NSAppleMusicUsageDescription',
        'label': 'Audio (音频)',
        'hint': '音频播放',
        'default_description': '此应用需要音频权限以播放声音'
    },
    'accessibility': {
        'key': 'NSAccessibilityUsageDescription',
        'label': 'Accessibility (辅助功能)',
        'hint': '全局快捷键、自动化',
        'default_description': '此应用需要辅助功能权限以监听键盘快捷键或自动化操作'
    },
    'documents_folder': {
        'key': 'NSDocumentsFolderUsageDescription',
        'label': 'Documents Folder (文档文件夹)',
        'hint': '读写文档',
        'default_description': '此应用需要访问文档文件夹以保存和读取用户数据'
    },
    'downloads_folder': {
        'key': 'NSDownloadsFolderUsageDescription',
        'label': 'Downloads Folder (下载文件夹)',
        'hint': '管理下载',
        'default_description': '此应用需要访问下载文件夹以管理下载的文件'
    },
    'apple_events': {
        'key': 'NSAppleEventsUsageDescription',
        'label': 'Apple Events (自动化)',
        'hint': 'AppleScript、应用间通信',
        'default_description': '此应用需要发送 Apple Events 以与其他应用程序交互'
    },
    'calendar': {
        'key': 'NSCalendarsUsageDescription',
        'label': 'Calendar (日历)',
        'hint': '读写日历事件',
        'default_description': '此应用需要访问日历以创建和管理日程'
    },
    'contacts': {
        'key': 'NSContactsUsageDescription',
        'label': 'Contacts (通讯录)',
        'hint': '读写联系人',
        'default_description': '此应用需要访问通讯录以管理联系人信息'
    },
    'location': {
        'key': 'NSLocationUsageDescription',
        'label': 'Location (位置)',
        'hint': '获取地理位置',
        'default_description': '此应用需要访问位置信息以提供基于位置的服务'
    },
    'photos': {
        'key': 'NSPhotoLibraryUsageDescription',
        'label': 'Photos (照片)',
        'hint': '访问相册',
        'default_description': '此应用需要访问照片库以选择和保存图片'
    },
}


# macOS 应用分类
MACOS_APP_CATEGORIES = {
    'productivity': 'public.app-category.productivity (效率工具)',
    'utilities': 'public.app-category.utilities (实用工具)',
    'business': 'public.app-category.business (商业)',
    'developer-tools': 'public.app-category.developer-tools (开发者工具)',
    'education': 'public.app-category.education (教育)',
    'entertainment': 'public.app-category.entertainment (娱乐)',
    'graphics-design': 'public.app-category.graphics-design (图形设计)',
    'music': 'public.app-category.music (音乐)',
}


# Linux 桌面分类
LINUX_DESKTOP_CATEGORIES = {
    'AudioVideo': 'AudioVideo (音视频)',
    'Audio': 'Audio (音频)',
    'Video': 'Video (视频)',
    'Development': 'Development (开发)',
    'Education': 'Education (教育)',
    'Game': 'Game (游戏)',
    'Graphics': 'Graphics (图形)',
    'Network': 'Network (网络)',
    'Office': 'Office (办公)',
    'Settings': 'Settings (设置)',
    'System': 'System (系统)',
    'Utility': 'Utility (实用工具)',
}


# Linux DEB 分类
LINUX_DEB_SECTIONS = {
    'admin': 'admin (系统管理)',
    'devel': 'devel (开发)',
    'utils': 'utils (实用工具)',
    'sound': 'sound (音频)',
    'net': 'net (网络)',
    'x11': 'x11 (图形界面)',
    'misc': 'misc (其他)',
}


# Linux RPM 分组
LINUX_RPM_GROUPS = {
    'Applications/System': 'Applications/System (系统应用)',
    'Applications/Utilities': 'Applications/Utilities (实用程序)',
    'Applications/Productivity': 'Applications/Productivity (效率工具)',
    'Applications/Multimedia': 'Applications/Multimedia (多媒体)',
    'Applications/Internet': 'Applications/Internet (互联网)',
    'Development/Tools': 'Development/Tools (开发工具)',
}


# Windows 安装程序语言
WINDOWS_LANGUAGES = {
    'chinesesimplified': '简体中文',
    # 'chinesetraditional': '繁體中文',
    'english': 'English',
    # 'japanese': '日本語',
    # 'korean': '한국어',
    # 'french': 'Français',
    # 'german': 'Deutsch',
    # 'spanish': 'Español',
}
