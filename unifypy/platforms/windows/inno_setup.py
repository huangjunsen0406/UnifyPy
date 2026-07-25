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
from .iss_builder import generate_iss_script, process_iss_template


class InnoSetupPackager(BasePackager):
    """
    Inno Setup 打包器.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._project_chinese_file = None  # 项目自带的中文语言文件路径
        self._check_project_language_file()
        
        # 初始化缓存管理器（使用项目根，而非进程 cwd）
        from ...utils.cache_manager import CacheManager
        self.cache_manager = CacheManager(str(self.project_dir))

    def _check_project_language_file(self):
        """
        检查项目是否自带中文语言文件.
        """
        try:
            import os

            # 多个可能的查找位置
            search_paths = []

            # 1. 基于配置文件路径的目录
            if self.config_file_path:
                config_dir = os.path.dirname(os.path.abspath(self.config_file_path))
                search_paths.append(os.path.join(config_dir, "ChineseSimplified.isl"))

            # 2. 当前工作目录
            search_paths.append(os.path.join(os.getcwd(), "ChineseSimplified.isl"))

            # 3. 项目根目录（如果 env_manager 可用）
            if hasattr(self, "env_manager") and hasattr(self.env_manager, "project_dir"):
                search_paths.append(os.path.join(self.env_manager.project_dir, "ChineseSimplified.isl"))

            # 尝试查找文件
            for chinese_file in search_paths:
                if os.path.exists(chinese_file):
                    self._project_chinese_file = chinese_file
                    if hasattr(self, "progress"):
                        self.progress.info(f"✅ 检测到项目自带的中文语言文件: {chinese_file}")
                    return

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

        # 处理 AppID：优先配置，否则 metadata，仅写 .unifypy/metadata.json（不改 build.json）
        app_id = self.cache_manager.get_or_generate_app_id(self.config)
        # Ensure in-memory config has app_id for ISS generation without rewriting build.json
        platforms = self.config.setdefault("platforms", {})
        windows = platforms.setdefault("windows", {})
        inno = windows.setdefault("inno_setup", {})
        if not inno.get("app_id"):
            inno["app_id"] = app_id
            self.progress.info(f"✅ AppID 已保存到 .unifypy/metadata.json: {app_id}")
        inno_config = self.get_format_config("inno_setup")

        # 创建 ISS 脚本
        iss_content = self._build_iss_script(inno_config, source_path, output_path)

        # 更新配置 hash（用于后续变化检测）
        self.cache_manager.save_config_hash(
            self.cache_manager.calculate_config_hash(self.config, "windows"),
            "windows"
        )

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
                command, "Windows打包", "正在生成Windows安装程序...", 80, shell=False
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
            except OSError:
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
        创建中文语言文件：优先从模板读取并写入目标路径。
        模板路径：unifypy/templates/ChineseSimplified.isl.template
        """
        try:
            # 尝试从模板读取
            template_candidates = [
                Path(__file__).parent.parent.parent / "templates" / "ChineseSimplified.isl.template",
                Path("unifypy/templates/ChineseSimplified.isl.template"),
                Path("templates/ChineseSimplified.isl.template"),
            ]

            content = None
            for p in template_candidates:
                if p.exists():
                    with open(p, "r", encoding="utf-8") as rf:
                        content = rf.read()
                    break

            if not content:
                # 模板缺失则放弃创建
                self.progress.warning("未找到 ChineseSimplified.isl 模板，跳过创建")
                return False

            with open(target_path, "w", encoding="utf-8-sig") as f:
                f.write(content)

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
            # 包内 templates 目录 (推荐位置)
            Path(__file__).parent.parent.parent / "templates" / "setup.iss.template",
            # 项目根目录下的 templates (兼容性)
            Path("templates/setup.iss.template"),
            Path("../templates/setup.iss.template"),
            # 绝对路径查找（包名迁移后）
            Path(__file__).parent.parent.parent.parent / "unifypy" / "templates" / "setup.iss.template",
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
        return process_iss_template(
            template_path=template_path,
            app_config=self.config,
            format_config=config,
            source_path=source_path,
            output_path=output_path,
            chinese_isl_path=self._get_chinese_isl_path(),
        )

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
        return generate_iss_script(
            app_config=self.config,
            format_config=config,
            source_path=source_path,
            output_path=output_path,
            project_chinese_file=getattr(self, "_project_chinese_file", None),
        )

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
