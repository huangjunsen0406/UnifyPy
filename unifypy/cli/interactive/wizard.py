#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交互式配置向导
引导用户生成 build.json 配置文件
"""

import json
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any

from .input_handlers import InputHandler
from .interactive_menu import InteractiveMenu
from .project_scanner import ProjectScanner
from .config_definitions import (
    MACOS_PERMISSIONS,
    MACOS_APP_CATEGORIES,
    LINUX_DESKTOP_CATEGORIES,
    WINDOWS_LANGUAGES,
)


class InteractiveWizard:
    """交互式配置向导"""

    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir).resolve()
        self.config: Dict[str, Any] = {}
        self.platforms: List[str] = []
        self.current_platform = self._detect_platform()

    def run(self) -> Optional[Path]:
        """
        运行向导，生成配置文件

        Returns:
            配置文件路径，如果取消则返回 None
        """
        try:
            self._show_banner()

            # 基础配置
            self._collect_basic_config()

            # 平台选择
            self._select_platforms()

            # PyInstaller 配置
            self._configure_pyinstaller()

            # 平台特定配置
            self.config['platforms'] = {}
            if 'macos' in self.platforms:
                self._configure_macos()
            if 'windows' in self.platforms:
                self._configure_windows()
            if 'linux' in self.platforms:
                self._configure_linux()

            # 显示摘要
            self._show_summary()

            # 保存配置
            if InputHandler.confirm("Save this configuration to build.json?", default=True):
                config_path = self._save_config()
                InputHandler.success(f"配置已保存到: {config_path}")

                # 提示可手动编辑
                InputHandler.info("你可以手动编辑 build.json 来调整配置，例如:")
                InputHandler.info("  - 修改权限描述文本")
                InputHandler.info("  - 添加更多 PyInstaller 选项 (hidden_import, exclude_module, etc.)")
                InputHandler.info("  - 自定义平台特定配置")

                return config_path
            else:
                print("\n❌ 已取消保存")
                return None

        except KeyboardInterrupt:
            print("\n\n⚠️  用户取消操作")
            return None
        except Exception as e:
            InputHandler.error(f"发生错误: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _show_banner(self):
        """显示欢迎横幅"""
        print()
        print("┌─────────────────────────────────────────────────────────────┐")
        print("│                                                             │")
        print("│  🚀 UnifyPy 2.0 - Interactive Configuration Wizard         │")
        print("│                                                             │")
        print("│  为你的 Python 项目生成打包配置                              │")
        print("│  💡 在任何输入提示处输入 ? 可查看详细帮助                     │")
        print("│                                                             │")
        print("└─────────────────────────────────────────────────────────────┘")
        print()

    def _detect_platform(self) -> str:
        """检测当前操作系统"""
        system = platform.system()
        if system == 'Darwin':
            return 'macos'
        elif system == 'Windows':
            return 'windows'
        elif system == 'Linux':
            return 'linux'
        return 'linux'

    def _collect_basic_config(self):
        """收集基础配置"""
        print("\n" + "=" * 60)
        print("基础配置 (Basic Configuration)")
        print("=" * 60 + "\n")

        # 项目目录（已通过命令行参数传入，仅显示）
        InputHandler.success(f"项目目录: {self.project_dir}")

        # 入口文件
        entry = InputHandler.text(
            "Entry file",
            default="main.py",
            required=True,
            help_text="Python 程序的主入口文件"
        )
        self.config['entry'] = entry

        # 项目名称
        default_name = Path(entry).stem
        name = InputHandler.text(
            "Project name",
            default=default_name,
            required=True,
            help_text="项目名称，用于生成可执行文件名"
        )
        self.config['name'] = name

        # 显示名称
        display_name = InputHandler.text(
            "Display name",
            default=name,
            help_text="应用程序显示名称"
        )
        if display_name:
            self.config['display_name'] = display_name

        # 版本号
        version = InputHandler.text(
            "Version",
            default="1.0.0",
            required=True,
            help_text="应用程序版本号"
        )
        self.config['version'] = version

        # 发布者
        publisher = InputHandler.text(
            "Publisher",
            help_text="发布者或公司名称"
        )
        if publisher:
            self.config['publisher'] = publisher

        # 描述
        description = InputHandler.text(
            "Description",
            help_text="应用程序简介"
        )
        if description:
            self.config['description'] = description

        # 图标路径
        icon = InputHandler.text(
            "Icon path",
            default="assets/icon.png",
            help_text="应用程序图标文件路径"
        )
        if icon:
            self.config['icon'] = icon

    def _select_platforms(self):
        """选择目标平台"""
        print("\n" + "=" * 60)
        print("目标平台 (Target Platforms)")
        print("=" * 60 + "\n")

        # 使用交互式多选菜单
        menu = InteractiveMenu()
        items = [
            ('macos', 'macOS (DMG/ZIP 安装包)'),
            ('windows', 'Windows (EXE 安装包)'),
            ('linux', 'Linux (DEB/RPM/AppImage)'),
        ]

        # 默认选中当前平台
        default_selected = [self.current_platform]

        selected = menu.show_menu(
            "选择目标平台 (Use arrow-keys, space to select, enter to confirm)",
            items,
            selected_items=default_selected
        )

        if not selected:
            InputHandler.info("未选择平台，默认使用当前平台")
            selected = [self.current_platform]

        self.platforms = selected
        platform_names = {'macos': 'macOS', 'windows': 'Windows', 'linux': 'Linux'}
        selected_names = [platform_names[p] for p in selected]
        InputHandler.success(f"已选择平台: {', '.join(selected_names)}")

    def _configure_pyinstaller(self):
        """配置 PyInstaller"""
        print("\n" + "=" * 60)
        print("PyInstaller 配置 (PyInstaller Configuration)")
        print("=" * 60 + "\n")

        self.config['pyinstaller'] = {}

        # 打包模式
        onefile = InputHandler.confirm(
            "Single file mode? (onefile: true)",
            default=False,
            help_text="Single file (true): 生成单文件; Directory (false): 生成目录"
        )
        self.config['pyinstaller']['onefile'] = onefile

        # 控制台模式
        windowed = InputHandler.confirm(
            "Windowed mode? (windowed: true, hide console)",
            default=False,
            help_text="Windowed (true): 隐藏控制台; Console (false): 显示控制台"
        )
        self.config['pyinstaller']['windowed'] = windowed

        # 数据目录
        InputHandler.info("正在扫描项目目录...")
        directories = ProjectScanner.scan_directories(self.project_dir)

        if directories:
            menu = InteractiveMenu()
            items = [(d['value'], f"{d['label']}  {InputHandler._color('gray', d['hint'])}")
                     for d in directories]

            # 默认选中推荐的目录
            default_selected = [d['value'] for d in directories if d.get('checked')]

            selected = menu.show_menu(
                "选择要打包的数据目录 (Use arrow-keys, space to select, enter to confirm)",
                items,
                selected_items=default_selected
            )

            if selected:
                self.config['pyinstaller']['add_data'] = [f"{d}:{d}" for d in selected]
                InputHandler.success(f"已选择 {len(selected)} 个目录: {', '.join(selected)}")
            else:
                InputHandler.info("未选择数据目录")
        else:
            InputHandler.info("未找到可打包的目录")

        # 清理和确认
        self.config['pyinstaller']['clean'] = True
        self.config['pyinstaller']['noconfirm'] = True

    def _configure_macos(self):
        """配置 macOS 平台"""
        print("\n" + "=" * 60)
        print("macOS 平台配置 (macOS Configuration)")
        print("=" * 60 + "\n")

        macos_config = {}

        # Bundle Identifier
        app_name = self.config.get('name', 'myapp').lower().replace(' ', '-')
        publisher = self.config.get('publisher', 'company').lower().replace(' ', '')
        default_bundle_id = f"com.{publisher}.{app_name}" if publisher else f"com.company.{app_name}"

        bundle_id = InputHandler.text(
            "Bundle Identifier",
            default=default_bundle_id,
            help_text="macOS 应用唯一标识符，格式: com.company.appname"
        )
        macos_config['bundle_identifier'] = bundle_id

        # 最低系统版本
        min_version = InputHandler.text(
            "Minimum macOS version",
            default="10.13",
            help_text="支持的最低 macOS 版本"
        )
        macos_config['minimum_system_version'] = min_version

        # 应用分类
        categories_items = [(k, v) for k, v in MACOS_APP_CATEGORIES.items()]
        menu = InteractiveMenu()
        category = menu.show_single_choice_menu(
            "选择应用分类",
            categories_items,
            default_key='productivity'
        )
        if category:
            macos_config['category'] = f"public.app-category.{category}"

        # 权限选择
        permissions_items = [(k, f"{v['label']}  {InputHandler._color('gray', v['hint'])}")
                              for k, v in MACOS_PERMISSIONS.items()]
        menu = InteractiveMenu()
        selected_permissions = menu.show_menu(
            "选择所需权限 (Use arrow-keys, space to select, enter to confirm)",
            permissions_items,
            selected_items=[]
        )

        if selected_permissions:
            for perm_key in selected_permissions:
                perm = MACOS_PERMISSIONS[perm_key]
                desc_key = f"{perm_key}_usage_description"
                macos_config[desc_key] = perm['default_description']

            InputHandler.success(f"已选择 {len(selected_permissions)} 个权限")
            InputHandler.info("💡 权限描述已使用通用文本，你可以在 build.json 中自定义描述")

        # 版权声明
        copyright_text = InputHandler.text(
            "Copyright notice",
            default=f"© 2024 {self.config.get('publisher', 'Company')}. All rights reserved.",
            help_text="版权声明文本"
        )
        if copyright_text:
            macos_config['copyright'] = copyright_text

        # DMG 配置（使用默认值）
        macos_config['dmg'] = {
            'volname': f"{self.config.get('display_name', self.config.get('name'))} 安装器",
            'window_size': [600, 450],
            'icon_size': 100,
            'format': 'UDZO'
        }

        self.config['platforms']['macos'] = macos_config

    def _configure_windows(self):
        """配置 Windows 平台"""
        print("\n" + "=" * 60)
        print("Windows 平台配置 (Windows Configuration)")
        print("=" * 60 + "\n")

        windows_config = {
            'inno_setup': {}
        }

        # 桌面图标
        create_desktop = InputHandler.confirm(
            "Create desktop icon?",
            default=True
        )
        windows_config['inno_setup']['create_desktop_icon'] = create_desktop

        # 开始菜单
        create_start_menu = InputHandler.confirm(
            "Create start menu shortcut?",
            default=True
        )
        windows_config['inno_setup']['create_start_menu_icon'] = create_start_menu

        # 安装后运行
        allow_run_after = InputHandler.confirm(
            "Allow run after install?",
            default=True
        )
        windows_config['inno_setup']['allow_run_after_install'] = allow_run_after

        # 语言选择
        language_items = [(k, v) for k, v in WINDOWS_LANGUAGES.items()]
        menu = InteractiveMenu()
        selected_languages = menu.show_menu(
            "选择安装程序语言 (Use arrow-keys, space to select, enter to confirm)",
            language_items,
            selected_items=['chinesesimplified', 'english']
        )

        if selected_languages:
            windows_config['inno_setup']['languages'] = selected_languages
            InputHandler.success(f"已选择 {len(selected_languages)} 种语言")

        self.config['platforms']['windows'] = windows_config

    def _configure_linux(self):
        """配置 Linux 平台"""
        print("\n" + "=" * 60)
        print("Linux 平台配置 (Linux Configuration)")
        print("=" * 60 + "\n")

        linux_config = {}

        # 包格式
        format_items = [
            ('deb', 'DEB (Debian/Ubuntu/Mint)'),
            ('rpm', 'RPM (RedHat/CentOS/Fedora)'),
            ('appimage', 'AppImage (通用格式，无需安装)'),
        ]
        menu = InteractiveMenu()
        selected_formats = menu.show_menu(
            "选择包格式 (Use arrow-keys, space to select, enter to confirm)",
            format_items,
            selected_items=['deb']
        )

        if not selected_formats:
            selected_formats = ['deb']

        linux_config['formats'] = selected_formats

        # 包名
        package_name = self.config.get('name', 'myapp').lower().replace(' ', '-')
        package_name = InputHandler.text(
            "Package name",
            default=package_name,
            help_text="包名称（小写，仅字母数字和连字符）"
        )

        # 桌面分类
        category_items = [(k, v) for k, v in LINUX_DESKTOP_CATEGORIES.items()]
        menu = InteractiveMenu()
        selected_categories = menu.show_menu(
            "选择桌面分类 (Use arrow-keys, space to select, enter to confirm)",
            category_items,
            selected_items=['Utility']
        )

        # DEB 配置
        if 'deb' in selected_formats:
            linux_config['deb'] = {
                'package': package_name,
                'section': 'utils',
                'priority': 'optional',
                'desktop_entry': True,
                'categories': selected_categories if selected_categories else ['Utility']
            }

        # RPM 配置
        if 'rpm' in selected_formats:
            linux_config['rpm'] = {
                'name': package_name,
                'group': 'Applications/Utilities'
            }

        # AppImage 配置
        if 'appimage' in selected_formats:
            linux_config['appimage'] = {
                'desktop_entry': True,
                'categories': selected_categories if selected_categories else ['Utility']
            }

        self.config['platforms']['linux'] = linux_config

    def _show_summary(self):
        """显示配置摘要"""
        print("\n" + "=" * 60)
        print("配置摘要 (Configuration Summary)")
        print("=" * 60 + "\n")

        print("📋 项目信息")
        print(f"  ✓ 名称: {self.config.get('name')} ({self.config.get('display_name', '')})")
        print(f"  ✓ 版本: {self.config.get('version')}")
        if self.config.get('publisher'):
            print(f"  ✓ 发布者: {self.config.get('publisher')}")
        if self.config.get('description'):
            print(f"  ✓ 描述: {self.config.get('description')}")
        print(f"  ✓ 图标: {self.config.get('icon', '未设置')}")
        print(f"  ✓ 入口: {self.config.get('entry')}")

        print("\n📦 打包配置")
        pyinstaller = self.config.get('pyinstaller', {})
        print(f"  ✓ 模式: {'Single file' if pyinstaller.get('onefile') else 'Directory'} (onefile: {pyinstaller.get('onefile')})")
        print(f"  ✓ 控制台: {'Windowed (hidden)' if pyinstaller.get('windowed') else 'Console (visible)'} (windowed: {pyinstaller.get('windowed')})")
        if pyinstaller.get('add_data'):
            data_dirs = [d.split(':')[0] for d in pyinstaller.get('add_data', [])]
            print(f"  ✓ 数据目录: {', '.join(data_dirs)} ({len(data_dirs)} 个)")

        print("\n🌍 目标平台")
        platform_names = {'macos': 'macOS', 'windows': 'Windows', 'linux': 'Linux'}
        for plat in self.platforms:
            print(f"  ✓ {platform_names.get(plat, plat)}")
            if plat == 'macos' and 'macos' in self.config.get('platforms', {}):
                macos_cfg = self.config['platforms']['macos']
                print(f"    - Bundle ID: {macos_cfg.get('bundle_identifier')}")
                # 统计权限数
                perm_count = sum(1 for k in macos_cfg.keys() if k.endswith('_usage_description'))
                if perm_count > 0:
                    print(f"    - 权限: {perm_count} 个")
            elif plat == 'linux' and 'linux' in self.config.get('platforms', {}):
                linux_cfg = self.config['platforms']['linux']
                formats = linux_cfg.get('formats', [])
                print(f"    - 格式: {', '.join([f.upper() for f in formats])}")

        print()

    def _save_config(self) -> Path:
        """保存配置文件"""
        config_path = self.project_dir / "build.json"

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

        return config_path
