#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows Inno Setup 打包器 支持完整的Inno Setup脚本配置.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from ..base import BasePackager


class InnoSetupPackager(BasePackager):
    """
    Inno Setup 打包器.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._project_chinese_file = None  # 项目自带的中文语言文件路径
        self._check_project_language_file()

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
                if hasattr(self, "tool_manager"):
                    self.progress.info("尝试自动获取Inno Setup...")
                    compiler_path = self.tool_manager.ensure_tool("inno-setup")
                else:
                    raise RuntimeError("ToolManager不可用")
            except Exception as e:
                self.progress.on_error(
                    Exception(f"未找到Inno Setup编译器: {e}"),
                    "Windows打包",
                    "请手动安装Inno Setup: https://jrsoftware.org/isinfo.php",
                )
                return False

        # 创建ISS脚本
        iss_content = self._build_iss_script(inno_config, source_path, output_path)

        # 写入临时ISS文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".iss", delete=False, encoding="utf-8"
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
            return inno_path

        # 自动检测Inno Setup安装
        detected_path = self._auto_detect_inno_setup()
        if detected_path:
            return detected_path

        # 检查PATH环境变量
        try:
            import shutil

            path_found = shutil.which("ISCC.exe")
            if path_found:
                return path_found
        except Exception:
            pass

        return None

    def _auto_detect_inno_setup(self) -> str:
        """
        自动检测Inno Setup安装路径.
        """
        # 检查注册表
        registry_path = self._check_registry_for_inno_setup()
        if registry_path and os.path.exists(registry_path):
            return registry_path

        # 检查常见安装路径
        common_paths = [
            r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            r"C:\Program Files\Inno Setup 6\ISCC.exe",
            r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
            r"C:\Program Files\Inno Setup 5\ISCC.exe",
            r"C:\Program Files (x86)\Inno Setup 4\ISCC.exe",
            r"C:\Program Files\Inno Setup 4\ISCC.exe",
        ]

        for path in common_paths:
            if os.path.exists(path):
                # 检查并设置语言文件
                self._setup_language_files(os.path.dirname(path))
                return path

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
        app_name = self.config.get("name", "MyApp")
        app_version = self.config.get("version", "1.0.0")
        publisher = self.config.get("publisher", "")
        app_url = config.get("app_url", "")

        # 确定源文件路径
        if source_path.is_file():
            # 单文件模式
            source_files = (
                f'Source: "{source_path}"; DestDir: "{{app}}"; Flags: ignoreversion'
            )
        else:
            # 目录模式
            source_files = f'Source: "{source_path}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs'

        # 构建Setup节
        setup_section = f"""[Setup]
AppId={{{config.get('app_id', f'{{{app_name}}}')}}}
AppName={app_name}
AppVersion={app_version}
AppVerName={app_name} {app_version}"""

        if publisher:
            setup_section += f"\nAppPublisher={publisher}"

        if app_url:
            setup_section += f"\nAppPublisherURL={app_url}"
            setup_section += f"\nAppSupportURL={app_url}"
            setup_section += f"\nAppUpdatesURL={app_url}"

        setup_section += f"""
DefaultDirName={{autopf}}\\{app_name}
DefaultGroupName={app_name}
AllowNoIcons=yes
LicenseFile={config.get('license_file', '')}
OutputDir={output_path.parent}
OutputBaseFilename={output_path.stem}
SetupIconFile={config.get('setup_icon', '')}
Compression=lzma
SolidCompression=yes
WizardStyle=modern"""

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

        # 图标节
        icons_section = "[Icons]"
        exe_name = source_path.name if source_path.is_file() else f"{app_name}.exe"
        icons_section += (
            f'\nName: "{{group}}\\{app_name}"; Filename: "{{app}}\\{exe_name}"'
        )

        if config.get("create_desktop_icon", True):
            icons_section += f'\nName: "{{autodesktop}}\\{app_name}"; Filename: "{{app}}\\{exe_name}"; Tasks: desktopicon'

        # 运行节
        run_section = "[Run]"
        if config.get("run_after_install", False):
            run_section += f'\nFilename: "{{app}}\\{exe_name}"; Description: "{{cm:LaunchProgram,{app_name}}}"; Flags: nowait postinstall skipifsilent'

        # 组装完整脚本
        iss_script = f"""; Script generated by UnifyPy 2.0
; Inno Setup Script

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

        # 检查许可证文件
        license_file = config.get("license_file")
        if license_file and not os.path.exists(license_file):
            errors.append(f"许可证文件不存在: {license_file}")

        # 检查图标文件
        setup_icon = config.get("setup_icon")
        if setup_icon and not os.path.exists(setup_icon):
            errors.append(f"安装程序图标文件不存在: {setup_icon}")

        return errors
