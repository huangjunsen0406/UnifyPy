#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows Inno Setup 打包器 支持完整的Inno Setup脚本配置.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import BasePackager


class InnoSetupPackager(BasePackager):
    """
    Inno Setup 打包器.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._project_chinese_file = None  # 项目自带的中文语言文件路径
        self._check_project_language_file()
        
        # 初始化缓存管理器
        from ...utils.cache_manager import CacheManager
        self.cache_manager = CacheManager(".")

    def _check_project_language_file(self):
        """
        检查项目是否自带中文语言文件.
        """
        try:
            # 尝试从当前工作目录查找
            import os

            current_dir = os.getcwd()
            chinese_file = os.path.join(current_dir, "ChineseSimplified.isl")

            if os.path.exists(chinese_file):
                self._project_chinese_file = chinese_file
                if hasattr(self, "progress"):
                    self.progress.info("✅ 检测到项目自带的中文语言文件")
        except Exception:
            pass  # 忽略错误，继续使用默认行为

    def get_supported_formats(self) -> List[str]:
        """
        获取支持的打包格式.
        """
        return ["exe"]

    def can_package_format(self, format_type: str) -> bool:
        """
        检查是否支持指定格式.
        """
        return format_type in self.get_supported_formats()

    def package(self, format_type: str, source_path: Path, output_path: Path) -> bool:
        """执行Inno Setup打包.

        Args:
            format_type: 打包格式 (exe)
            source_path: PyInstaller生成的可执行文件路径
            output_path: 输出安装包路径

        Returns:
            bool: 打包是否成功
        """
        if not self.can_package_format(format_type):
            self.progress.on_error(
                Exception(f"不支持的格式: {format_type}"), "Windows打包"
            )
            return False

        # 获取Inno Setup配置
        inno_config = self.get_format_config("inno_setup")

        # 检查Inno Setup编译器
        compiler_path = self._find_inno_setup_compiler()
        if not compiler_path:
            # 尝试使用ToolManager自动获取
            try:
                if hasattr(self, "tool_manager") and self.tool_manager:
                    self.progress.info("🔄 尝试通过ToolManager获取Inno Setup...")
                    compiler_path = self.tool_manager.ensure_tool("inno-setup")
                    if compiler_path:
                        self.progress.info(f"✅ ToolManager找到Inno Setup: {compiler_path}")
                else:
                    raise RuntimeError("ToolManager不可用")
            except Exception as e:
                self.progress.on_error(
                    Exception(f"未找到Inno Setup编译器: {e}"),
                    "Windows打包",
                    "解决方案:\n1. 手动安装Inno Setup: https://jrsoftware.org/isinfo.php\n2. 或在配置中指定路径: 'inno_setup_path': 'C:\\\\path\\\\to\\\\ISCC.exe'",
                )
                return False

        # 智能缓存管理：检查是否需要重新生成 ISS 脚本
        use_cached_iss = False
        cached_iss_content = None
        
        if not self.cache_manager.should_regenerate_config(self.config, "windows"):
            # 配置未变化，尝试使用缓存的 ISS 文件
            cached_iss_content = self.cache_manager.load_cached_file("windows", "iss")
            if cached_iss_content:
                use_cached_iss = True
                self.progress.info("✅ 使用缓存的 ISS 配置")
        
        if not use_cached_iss:
            # 需要重新生成 ISS 脚本
            self.progress.info("🔄 生成新的 ISS 配置")
            
            # 处理 AppID：确保存在并写回配置文件
            app_id = self.cache_manager.get_or_generate_app_id(self.config)
            if not self.config.get("platforms", {}).get("windows", {}).get("inno_setup", {}).get("app_id"):
                # AppID 不在配置中，需要写回
                if self.cache_manager.update_build_config_with_app_id(self.config_file_path, app_id):
                    self.progress.info(f"✅ AppID 已写入配置文件: {app_id}")
                    # 重新加载配置以包含新的 AppID
                    import json
                    try:
                        with open(self.config_file_path, "r", encoding="utf-8") as f:
                            updated_config = json.load(f)
                        self.config = updated_config
                        inno_config = self.get_format_config("inno_setup")
                    except Exception as e:
                        self.progress.warning(f"重新加载配置失败: {e}")
            
            # 创建ISS脚本
            iss_content = self._build_iss_script(inno_config, source_path, output_path)
            
            # 缓存生成的 ISS 文件
            self.cache_manager.save_cached_file("windows", "iss", iss_content)
            self.cache_manager.save_config_hash(
                self.cache_manager.calculate_config_hash(self.config, "windows"), 
                "windows"
            )
            self.progress.info("💾 ISS 配置已缓存")
        else:
            iss_content = cached_iss_content

        # 写入临时ISS文件 - 使用UTF-8 BOM编码确保中文字符正确显示
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".iss", delete=False, encoding="utf-8-sig"
        ) as f:
            f.write(iss_content)
            iss_file = f.name

        try:
            # 执行编译
            command = [compiler_path, "/Q", iss_file]

            success = self.runner.run_command(
                command, "Windows打包", f"正在生成Windows安装程序...", 80, shell=False
            )

            if success:
                self.progress.update_stage("Windows打包", 10, "验证输出文件")
                if output_path.exists():
                    return True
                else:
                    self.progress.on_error(
                        Exception(f"输出文件不存在: {output_path}"), "Windows打包"
                    )
                    return False
            else:
                return False

        finally:
            # 清理临时文件
            try:
                os.unlink(iss_file)
            except:
                pass

    def _find_inno_setup_compiler(self) -> str:
        """
        查找Inno Setup编译器.
        """
        # 首先检查配置中的路径
        inno_path = self.config.get("inno_setup_path")
        if inno_path and os.path.exists(inno_path):
            if hasattr(self, "progress"):
                self.progress.info(f"✅ 使用配置中的 Inno Setup 路径: {inno_path}")
            return inno_path

        # 检查PATH环境变量
        try:
            import shutil
            path_found = shutil.which("ISCC.exe")
            if path_found:
                if hasattr(self, "progress"):
                    self.progress.info(f"✅ 在PATH中找到 Inno Setup: {path_found}")
                return path_found
        except Exception:
            pass

        # 自动检测Inno Setup安装
        detected_path = self._auto_detect_inno_setup()
        if detected_path:
            if hasattr(self, "progress"):
                self.progress.info(f"✅ 自动检测到 Inno Setup: {detected_path}")
            return detected_path

        return None

    def _auto_detect_inno_setup(self) -> str:
        """
        自动检测Inno Setup安装路径.
        """
        # 检查注册表
        registry_path = self._check_registry_for_inno_setup()
        if registry_path and os.path.exists(registry_path):
            return registry_path

        # 检查常见安装路径（按版本从新到旧）
        common_paths = [
            r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            r"C:\Program Files\Inno Setup 6\ISCC.exe",
            r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
            r"C:\Program Files\Inno Setup 5\ISCC.exe",
        ]

        if hasattr(self, "progress"):
            self.progress.info("🔍 搜索 Inno Setup 安装路径...")

        for path in common_paths:
            if os.path.exists(path):
                # 检查并设置语言文件
                self._setup_language_files(os.path.dirname(path))
                return path

        if hasattr(self, "progress"):
            self.progress.warning("⚠️ 未找到 Inno Setup 安装，请手动安装或在配置中指定路径")

        return None

    def _check_registry_for_inno_setup(self) -> str:
        """
        从Windows注册表检查Inno Setup安装路径.
        """
        try:
            import winreg

            # 检查不同版本的注册表项
            registry_keys = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1",
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 5_is1",
                r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1",
                r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 5_is1",
            ]

            for key_path in registry_keys:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        install_location, _ = winreg.QueryValueEx(
                            key, "InstallLocation"
                        )
                        if install_location:
                            iscc_path = os.path.join(install_location, "ISCC.exe")
                            if os.path.exists(iscc_path):
                                # 设置语言文件
                                self._setup_language_files(install_location)
                                return iscc_path
                except (FileNotFoundError, OSError):
                    continue

        except ImportError:
            # winreg模块不可用（非Windows系统）
            pass
        except Exception as e:
            self.progress.warning(f"检查注册表时出错: {e}")

        return None

    def _setup_language_files(self, inno_setup_dir: str):
        """
        设置Inno Setup语言文件.
        """
        # 如果项目已经提供了中文语言文件，就不需要检查系统文件了
        if self._project_chinese_file:
            return

        # 检查 Inno Setup 系统目录
        languages_dir = os.path.join(inno_setup_dir, "Languages")

        if not os.path.exists(languages_dir):
            return

        # 检查系统中文语言文件
        chinese_file = os.path.join(languages_dir, "ChineseSimplified.isl")

        if not os.path.exists(chinese_file):
            self.progress.info("正在下载中文语言文件...")
            success = self._download_chinese_language_file(chinese_file)
            if success:
                self.progress.info("✅ 中文语言文件已安装")
            else:
                self.progress.warning("❌ 中文语言文件下载失败，将只支持英语界面")
        else:
            self.progress.info("✅ 检测到中文语言文件支持")

    def _download_chinese_language_file(self, target_path: str) -> bool:
        """
        下载中文语言文件.
        """
        try:
            import urllib.request

            # Inno Setup官方中文语言文件URL
            language_urls = [
                "https://raw.githubusercontent.com/jrsoftware/issrc/main/Files/Languages/Unofficial/ChineseSimplified.isl",
                "https://github.com/jrsoftware/issrc/raw/main/Files/Languages/Unofficial/ChineseSimplified.isl",
            ]

            for url in language_urls:
                try:
                    self.progress.info(f"从 {url} 下载...")
                    urllib.request.urlretrieve(url, target_path)

                    # 验证文件
                    if (
                        os.path.exists(target_path)
                        and os.path.getsize(target_path) > 100
                    ):
                        return True
                    else:
                        os.remove(target_path) if os.path.exists(target_path) else None

                except Exception as e:
                    self.progress.warning(f"从 {url} 下载失败: {e}")
                    continue

            # 如果下载失败，创建一个基本的中文语言文件
            return self._create_basic_chinese_language_file(target_path)

        except Exception as e:
            self.progress.warning(f"下载中文语言文件时出错: {e}")
            return False

    def _create_basic_chinese_language_file(self, target_path: str) -> bool:
        """
        创建基本的中文语言文件.
        """
        try:
            chinese_isl_content = """[LangOptions]
LanguageName=中文(简体)
LanguageID=$0804
LanguageCodePage=936

[Messages]
; 基本安装消息
SetupAppTitle=安装程序
SetupWindowTitle=安装 - %1
UninstallAppTitle=卸载程序
UninstallAppFullTitle=%1 卸载程序

; 通用按钮和标签
ButtonBack=< 上一步(&B)
ButtonNext=下一步(&N) >
ButtonInstall=安装(&I)
ButtonCancel=取消
ButtonYes=是(&Y)
ButtonNo=否(&N)
ButtonFinish=完成(&F)
ButtonBrowse=浏览(&B)...
ButtonWizardBrowse=浏览(&R)...

; 安装类型
SelectDirLabel3=安装程序将把 [name] 安装到下列文件夹中。
SelectDirBrowseLabel=单击"下一步"继续。如果您想选择其他文件夹，请单击"浏览"。
DiskSpaceMBLabel=至少需要 [mb] MB 的可用磁盘空间。

; 准备安装
WizardPreparing=正在准备安装
PreparingDesc=安装程序正在准备安装 [name] 到您的计算机上。

; 正在安装
WizardInstalling=正在安装
InstallingLabel=请等待，安装程序正在安装 [name] 到您的计算机上。

; 完成安装
FinishedHeadingLabel=正在完成 [name] 安装向导
FinishedLabelNoIcons=安装程序已在您的计算机上安装了 [name]。
FinishedLabel=安装程序已在您的计算机上安装了 [name]。可以通过选择安装的图标来运行此应用程序。
ClickFinish=单击"完成"退出安装程序。

; 错误消息
ErrorFunctionFailedNoCode=%1 失败
ErrorFunctionFailed=%1 失败；代码 %2
ErrorFunctionFailedWithMessage=%1 失败；代码 %2.%n%3
ErrorExecutingProgram=无法执行文件：%n%1

; 状态消息
StatusExtractFiles=正在解压文件...
StatusCreateDirs=正在创建目录...
StatusRestartComputer=安装程序将重新启动计算机...

; 其他
NameAndVersion=%1 版本 %2
AdditionalIcons=附加图标：
CreateDesktopIcon=创建桌面图标(&D)
CreateQuickLaunchIcon=创建快速启动图标(&Q)
ProgramOnTheWeb=%1 网站
UninstallProgram=卸载 %1
LaunchProgram=运行 %1
AssocFileExtension=将 %1 与 %2 文件扩展名关联(&A)
AssocingFileExtension=正在将 %1 与 %2 文件扩展名关联...
AutoStartProgramGroupDescription=启动：
AutoStartProgram=自动启动 %1
AddonHostProgramNotFound=%1 无法在您选择的文件夹中找到。%n%n无论如何都要继续吗？
"""

            with open(target_path, "w", encoding="utf-8-sig") as f:
                f.write(chinese_isl_content)

            return True

        except Exception as e:
            self.progress.warning(f"创建中文语言文件失败: {e}")
            return False

    def _build_iss_script(
        self, config: Dict[str, Any], source_path: Path, output_path: Path
    ) -> str:
        """
        构建Inno Setup脚本.
        """
        # 尝试使用模板文件
        template_path = self._find_iss_template()
        if template_path:
            return self._process_template(template_path, config, source_path, output_path)
        else:
            # 回退到内置生成逻辑
            return self._generate_iss_script(config, source_path, output_path)

    def _find_iss_template(self) -> Optional[Path]:
        """
        查找ISS模板文件.
        """
        # 查找模板文件的可能位置
        template_locations = [
            # src/templates 目录 (推荐位置)
            Path(__file__).parent.parent.parent / "templates" / "setup.iss.template",
            # 项目根目录下的 templates (兼容性)
            Path("templates/setup.iss.template"),
            Path("../templates/setup.iss.template"),
            # 绝对路径查找
            Path(__file__).parent.parent.parent.parent / "src" / "templates" / "setup.iss.template",
        ]
        
        if hasattr(self, "progress"):
            self.progress.info("🔍 查找 ISS 模板文件...")
        
        for location in template_locations:
            if location.exists():
                if hasattr(self, "progress"):
                    self.progress.info(f"✅ 找到模板文件: {location}")
                return location
                
        if hasattr(self, "progress"):
            self.progress.info("⚠️ 未找到模板文件，使用内置生成器")
        return None

    def _process_template(
        self, template_path: Path, config: Dict[str, Any], source_path: Path, output_path: Path
    ) -> str:
        """
        处理ISS模板文件.
        """
        app_name = self.config.get("name", "MyApp")
        app_version = self.config.get("version", "1.0.0")
        publisher = self.config.get("publisher", "Unknown Publisher")
        app_url = config.get("app_url", "")
        display_name = self.config.get("display_name", app_name)
        
        # 生成APP_ID - 修复格式问题
        app_id = config.get('app_id', None)
        if not app_id:
            # 生成基于应用名称的伪GUID格式，注意这里不包含花括号
            import hashlib
            name_hash = hashlib.md5(app_name.encode()).hexdigest()[:8].upper()
            app_id = f"C4D8B3F2-1234-5678-9ABC-{name_hash}12345678"
        elif app_id.startswith('{') and app_id.endswith('}'):
            # 移除现有的花括号，因为模板中已经有了
            app_id = app_id.strip('{}')

        # 确定源文件路径和可执行文件名
        source_path_str = str(source_path).replace('/', '\\')
        
        if source_path.is_file():
            # 单文件模式
            source_files = f'Source: "{source_path_str}"; DestDir: "{{app}}"; Flags: ignoreversion'
            exe_name = source_path.name
        else:
            # 目录模式
            source_files = f'Source: "{source_path_str}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs'
            exe_name = f"{app_name}.exe"

        # 读取模板内容
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # 替换模板变量
        replacements = {
            '{{APP_ID}}': app_id,
            '{{APP_NAME}}': app_name,
            '{{APP_VERSION}}': app_version,
            '{{APP_DISPLAY_NAME}}': display_name,
            '{{APP_PUBLISHER}}': publisher,
            '{{APP_URL}}': app_url,
            '{{OUTPUT_DIR}}': str(output_path.parent).replace('/', '\\'),
            '{{OUTPUT_FILENAME}}': output_path.stem,
            '{{SOURCE_FILES}}': source_files,
            '{{EXE_NAME}}': exe_name,
        }

        # 条件块处理
        conditions = {
            '{{#APP_URL}}': bool(app_url),
            '{{#LICENSE_FILE}}': bool(config.get('license_file')) and os.path.exists(config.get('license_file', '')),
            '{{#SETUP_ICON}}': bool(config.get('setup_icon')) and os.path.exists(config.get('setup_icon', '')),
            '{{#CREATE_DESKTOP_ICON}}': config.get('create_desktop_icon', True),
            '{{#CREATE_START_MENU_ICON}}': config.get('create_start_menu_icon', False),
            '{{#RUN_AFTER_INSTALL}}': config.get('run_after_install', False),
            '{{#CHINESE_SUPPORT}}': 'chinesesimplified' in config.get('languages', []) or 'chinese' in config.get('languages', []),
        }

        # 处理条件块 - 改进的处理逻辑
        result = template_content
        for condition, should_include in conditions.items():
            start_tag = condition
            end_tag = condition.replace('#', '/')
            
            # 查找条件块
            start_idx = result.find(start_tag)
            while start_idx != -1:
                end_idx = result.find(end_tag, start_idx)
                if end_idx == -1:
                    break
                    
                if should_include:
                    # 保留内容，移除标记
                    content = result[start_idx + len(start_tag):end_idx]
                    result = result[:start_idx] + content + result[end_idx + len(end_tag):]
                    start_idx = result.find(start_tag, start_idx + len(content))
                else:
                    # 移除整个块
                    result = result[:start_idx] + result[end_idx + len(end_tag):]
                    start_idx = result.find(start_tag, start_idx)

        # 处理特殊替换
        if conditions['{{#LICENSE_FILE}}']:
            result = result.replace('{{LICENSE_FILE}}', str(Path(config.get('license_file')).resolve()).replace('/', '\\'))
        
        if conditions['{{#SETUP_ICON}}']:
            result = result.replace('{{SETUP_ICON}}', str(Path(config.get('setup_icon')).resolve()).replace('/', '\\'))
            
        if conditions['{{#CHINESE_SUPPORT}}']:
            chinese_isl_path = self._get_chinese_isl_path()
            result = result.replace('{{CHINESE_ISL_PATH}}', chinese_isl_path)
        
        # 清理其他特殊标记
        result = result.replace('{{LICENSE_FILE}}', '')
        result = result.replace('{{SETUP_ICON}}', '')
        result = result.replace('{{CHINESE_ISL_PATH}}', '')

        # 执行基本替换
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)

        # 清理剩余的模板标记
        import re
        # 移除任何剩余的 {{#...}} 和 {{/...}} 标记
        result = re.sub(r'\{\{[#/][^}]+\}\}', '', result)
        # 移除多余的空行
        result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)
        
        return result.strip()

    def _get_chinese_isl_path(self) -> str:
        """
        获取中文ISL文件路径.
        """
        if self._project_chinese_file:
            return str(Path(self._project_chinese_file).resolve()).replace('/', '\\')
        else:
            return 'compiler:Languages\\ChineseSimplified.isl'

    def _generate_iss_script(
        self, config: Dict[str, Any], source_path: Path, output_path: Path
    ) -> str:
        """
        内置ISS脚本生成逻辑 (回退方案).
        """
        app_name = self.config.get("name", "MyApp")
        app_version = self.config.get("version", "1.0.0")
        publisher = self.config.get("publisher", "Unknown Publisher")
        app_url = config.get("app_url", "")
        display_name = self.config.get("display_name", app_name)

        # 确定源文件路径 - 修复路径分隔符问题
        source_path_str = str(source_path).replace('/', '\\')
        
        if source_path.is_file():
            # 单文件模式
            source_files = f'Source: "{source_path_str}"; DestDir: "{{app}}"; Flags: ignoreversion'
            exe_name = source_path.name
        else:
            # 目录模式 - 确保正确的通配符路径
            source_files = f'Source: "{source_path_str}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs'
            # 在目录模式下，可执行文件通常是 app_name.exe
            exe_name = f"{app_name}.exe"

        # 构建Setup节 - 修复路径问题和空值处理
        app_id = config.get('app_id', None)
        if not app_id:
            # 生成基于应用名称的伪GUID格式
            import hashlib
            name_hash = hashlib.md5(app_name.encode()).hexdigest()[:8].upper()
            app_id = f"{{C4D8B3F2-1234-5678-9ABC-{name_hash}12345678}}"
        elif not (app_id.startswith('{') and app_id.endswith('}')):
            # 确保使用花括号格式
            app_id = f"{{{app_id}}}"
        
        # 处理路径中的反斜杠
        output_dir = str(output_path.parent).replace('/', '\\')
        
        setup_section = f"""[Setup]
AppId={app_id}
AppName={app_name}
AppVersion={app_version}
AppVerName={display_name} {app_version}
AppPublisher={publisher}
DefaultDirName={{autopf}}\\{app_name}
DefaultGroupName={app_name}
AllowNoIcons=yes
OutputDir={output_dir}
OutputBaseFilename={output_path.stem}
Compression=lzma
SolidCompression=yes
WizardStyle=modern"""

        # 只在存在时添加可选字段
        if app_url:
            setup_section += f"\nAppPublisherURL={app_url}"
            setup_section += f"\nAppSupportURL={app_url}"
            setup_section += f"\nAppUpdatesURL={app_url}"

        license_file = config.get('license_file', '')
        if license_file and os.path.exists(license_file):
            license_path = str(Path(license_file)).replace('/', '\\')
            setup_section += f"\nLicenseFile={license_path}"

        setup_icon = config.get('setup_icon', '')
        if setup_icon and os.path.exists(setup_icon):
            setup_icon_path = str(Path(setup_icon)).replace('/', '\\')
            setup_section += f"\nSetupIconFile={setup_icon_path}"

        # 语言支持
        languages_section = "[Languages]"
        languages = config.get("languages", ["english"])
        if "english" in languages:
            languages_section += (
                '\nName: "english"; MessagesFile: "compiler:Default.isl"'
            )
        if "chinesesimplified" in languages or "chinese" in languages:
            # 优先使用项目自带的中文语言文件
            if hasattr(self, "_project_chinese_file") and self._project_chinese_file:
                # 使用项目自带的语言文件，需要转换为相对路径或绝对路径
                chinese_file_path = os.path.abspath(self._project_chinese_file).replace(
                    "\\", "\\\\"
                )
                languages_section += (
                    f'\nName: "chinesesimplified"; MessagesFile: "{chinese_file_path}"'
                )
            else:
                # 使用系统中的语言文件
                languages_section += '\nName: "chinesesimplified"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"'

        # 任务节
        tasks_section = "[Tasks]"
        if config.get("create_desktop_icon", True):
            tasks_section += f'\nName: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked'

        # 文件节
        files_section = f"[Files]\n{source_files}"

        # 图标节 - 使用 display_name 作为快捷方式名称
        icons_section = "[Icons]"
        icons_section += f'\nName: "{{group}}\\{display_name}"; Filename: "{{app}}\\{exe_name}"'

        if config.get("create_desktop_icon", True):
            icons_section += f'\nName: "{{autodesktop}}\\{display_name}"; Filename: "{{app}}\\{exe_name}"; Tasks: desktopicon'
        
        # 添加卸载程序快捷方式
        icons_section += f'\nName: "{{group}}\\{{cm:UninstallProgram,{display_name}}}"; Filename: "{{uninstallexe}}"'

        # 运行节
        run_section = "[Run]"
        if config.get("run_after_install", False):
            run_section += f'\nFilename: "{{app}}\\{exe_name}"; Description: "{{cm:LaunchProgram,{display_name}}}"; Flags: nowait postinstall skipifsilent'

        # 组装完整脚本
        iss_script = f"""; Script generated by UnifyPy 2.0
; Inno Setup Script
; Encoding: UTF-8

{setup_section}

{languages_section}

{tasks_section}

{files_section}

{icons_section}

{run_section}
"""

        return iss_script

    def validate_config(self, format_type: str) -> List[str]:
        """
        验证Inno Setup配置.
        """
        errors = []

        config = self.get_format_config("inno_setup")

        # 检查Inno Setup编译器
        compiler_path = self._find_inno_setup_compiler()
        if not compiler_path:
            errors.append("未找到Inno Setup编译器 (ISCC.exe)。请安装Inno Setup或在配置中指定路径")

        # 检查许可证文件
        license_file = config.get("license_file")
        if license_file and not os.path.exists(license_file):
            errors.append(f"许可证文件不存在: {license_file}")

        # 检查图标文件
        setup_icon = config.get("setup_icon")
        if setup_icon and not os.path.exists(setup_icon):
            errors.append(f"安装程序图标文件不存在: {setup_icon}")

        return errors
