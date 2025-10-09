#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UnifyPy 2.0 - 跨平台Python应用打包工具
重构版本，支持进度条、配置归一化、多格式打包等
"""

import argparse
import os
import platform
import sys
from pathlib import Path
from typing import List, Optional

from src.core.config import ConfigManager
from src.platforms.registry import PackagerRegistry
from src.pyinstaller.config_builder import PyInstallerConfigBuilder
from src.utils.command_runner import SilentRunner
from src.utils.file_ops import FileOperations
from src.utils.info_plist_updater import InfoPlistUpdater
from src.utils.macos_codesign import MacOSCodeSigner
from src.utils.parallel_builder import ParallelBuilder
from src.utils.progress import ProgressManager
from src.utils.rollback import RollbackManager
from src.utils.tool_manager import ToolManager
from src.utils.cache_manager import CacheManager

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def parse_arguments():
    """
    解析命令行参数.
    """
    parser = argparse.ArgumentParser(
        description="UnifyPy 2.0 - 跨平台Python应用打包工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py . --config build.json
  python main.py /path/to/project --name myapp --version 1.0.0
  python main.py . --config build.json --verbose
        """,
    )

    parser.add_argument("project_dir", help="Python项目根目录路径")
    parser.add_argument("--config", help="配置文件路径 (JSON格式)", default=None)

    # 基本信息
    parser.add_argument("--name", help="应用程序名称", default=None)
    parser.add_argument("--display-name", help="应用程序显示名称", default=None)
    parser.add_argument("--entry", help="入口Python文件", default="main.py")
    parser.add_argument("--version", help="应用程序版本", default="1.0.0")
    parser.add_argument("--publisher", help="发布者名称", default=None)

    # 文件和资源
    parser.add_argument("--icon", help="图标文件路径", default=None)
    parser.add_argument("--license", help="许可证文件路径", default=None)
    parser.add_argument("--readme", help="自述文件路径", default=None)
    parser.add_argument("--hooks", help="运行时钩子目录", default=None)

    # PyInstaller选项
    parser.add_argument(
        "--onefile", help="生成单文件模式的可执行文件", action="store_true"
    )
    parser.add_argument(
        "--windowed", help="窗口模式（不显示控制台）", action="store_true"
    )
    parser.add_argument("--console", help="控制台模式", action="store_true")

    # 构建选项
    parser.add_argument("--skip-exe", help="跳过可执行文件构建", action="store_true")
    parser.add_argument(
        "--skip-installer", help="跳过安装程序构建", action="store_true"
    )
    parser.add_argument("--clean", help="清理之前的构建文件", action="store_true")

    # 工具路径
    parser.add_argument(
        "--inno-setup-path", help="Inno Setup可执行文件路径", default=None
    )

    # 输出控制
    parser.add_argument("--verbose", "-v", help="显示详细输出", action="store_true")
    parser.add_argument("--quiet", "-q", help="静默模式", action="store_true")

    # 平台选项
    parser.add_argument(
        "--format", help="输出格式 (exe,dmg,pkg,deb,rpm,appimage)", default=None
    )

    # 性能选项
    parser.add_argument("--parallel", help="启用并行构建", action="store_true")
    parser.add_argument(
        "--max-workers", help="最大并行工作线程数", type=int, default=None
    )

    # 回滚选项
    parser.add_argument("--no-rollback", help="禁用自动回滚", action="store_true")
    parser.add_argument("--rollback", help="执行指定会话的回滚", metavar="SESSION_ID")
    parser.add_argument(
        "--list-rollback", help="列出可用的回滚会话", action="store_true"
    )

    # macOS 开发选项
    parser.add_argument(
        "--development", help="强制开发版本（启用调试权限）", action="store_true"
    )
    parser.add_argument(
        "--production",
        help="生产版本（禁用调试权限，仅用于签名应用）",
        action="store_true",
    )

    return parser.parse_args()


class UnifyPyBuilder:
    """
    UnifyPy 2.0 主构建器.
    """

    def __init__(self, args):
        """初始化构建器.

        Args:
            args: 命令行参数
        """
        self.args = args
        self.project_dir = Path(args.project_dir).resolve()

        # 初始化组件
        self.progress = ProgressManager(verbose=args.verbose)
        self.runner = SilentRunner(self.progress)
        self.file_ops = FileOperations()
        self.tool_manager = ToolManager()

        # 配置管理
        try:
            self.config = ConfigManager(
                config_path=args.config,
                args=vars(args),
            )
        except Exception as e:
            print(f"❌ 配置加载失败: {e}")
            sys.exit(1)

        # PyInstaller 配置构建器
        self.pyinstaller_builder = PyInstallerConfigBuilder(verbose=args.verbose)

        # Info.plist 更新器（macOS 专用）
        self.info_plist_updater = InfoPlistUpdater(verbose=args.verbose)

        # macOS 代码签名器
        self.macos_codesigner = MacOSCodeSigner(verbose=args.verbose)

        # 平台打包器注册表
        self.packager_registry = PackagerRegistry()

        # 构建环境
        self.temp_dir = None
        self.dist_dir = self.project_dir / "dist"
        self.installer_dir = self.project_dir / "installer"

    def run(self) -> int:
        """运行构建过程.

        Returns:
            int: 退出码
        """
        # 处理回滚相关命令
        if self.args.list_rollback:
            return self._list_rollback_sessions()

        if self.args.rollback:
            return self._execute_rollback(self.args.rollback)

        # 正常构建流程
        rollback_manager = None
        if not self.args.no_rollback:
            rollback_manager = RollbackManager(self.project_dir, self.progress)

        try:
            if rollback_manager:
                with rollback_manager:
                    return self._run_build_process(rollback_manager)
            else:
                return self._run_build_process(None)

        except KeyboardInterrupt:
            self.progress.on_error(Exception("用户中断"), "构建过程")
            return 1
        except Exception as e:
            self.progress.on_error(e, "构建过程")
            return 1
        finally:
            self._cleanup()
            self.progress.stop()

    def _run_build_process(self, rollback_manager: Optional[RollbackManager]) -> int:
        """
        运行实际的构建过程.
        """
        self.progress.start()

        # 验证项目
        self._validate_project()

        # 准备环境
        self._prepare_environment(rollback_manager)

        # 构建可执行文件
        if not self.args.skip_exe:
            self._build_executable(rollback_manager)

        # 构建安装包
        if not self.args.skip_installer:
            self._build_installer(rollback_manager)

        # 显示成功信息
        self._show_success()

        return 0

    def _validate_project(self):
        """
        验证项目结构和配置.
        """
        stage = "环境检查"
        self.progress.start_stage(stage, "验证项目配置和依赖")

        # 检查项目目录
        if not self.project_dir.exists():
            raise FileNotFoundError(f"项目目录不存在: {self.project_dir}")

        self.progress.update_stage(stage, 10, "检查入口文件", absolute=True)

        # 检查入口文件
        entry_file = self.config.resolve_path(self.config.get("entry"))
        if not entry_file.exists():
            raise FileNotFoundError(f"入口文件不存在: {entry_file}")

        self.progress.update_stage(stage, 20, "检查PyInstaller", absolute=True)

        # 检查PyInstaller
        if not self.runner.check_tool_available("pyinstaller"):
            raise RuntimeError("PyInstaller未安装，请运行: pip install pyinstaller")

        self.progress.update_stage(stage, 40, "检查平台打包器", absolute=True)

        # 检查平台特定的打包器工具
        if not self.args.skip_installer:
            self._check_packager_tools()

        self.progress.update_stage(stage, 70, "检查磁盘空间", absolute=True)

        # 检查磁盘空间
        if not self.file_ops.check_disk_space(str(self.project_dir), 500):
            self.progress.warning("磁盘空间可能不足（建议至少500MB）")

        self.progress.complete_stage(stage)

    def _check_packager_tools(self):
        """
        检查平台特定的打包器工具是否可用.
        如果工具不存在，提示下载地址.
        """
        current_platform = self.config.current_platform

        # 获取需要检测的工具
        required_tools = self.tool_manager.get_required_tools_for_platform(
            current_platform
        )

        if not required_tools:
            # 没有需要检测的工具
            return

        missing_tools = []

        for tool_info in required_tools:
            tool_name = tool_info["name"]
            tool_display_name = tool_info["display_name"]

            # 检查工具是否可用
            is_available = self.tool_manager.check_tool_available(tool_name)

            if not is_available:
                missing_tools.append(tool_info)
                self.progress.warning(f"⚠️  未找到 {tool_display_name}")

        # 如果有缺失的工具，显示详细信息并退出
        if missing_tools:
            print("\n" + "="*70)
            print("❌ 缺少必要的打包工具")
            print("="*70)

            for tool_info in missing_tools:
                print(f"\n📦 工具: {tool_info['display_name']}")
                print(f"   描述: {tool_info['description']}")
                print(f"   下载地址: {tool_info['download_url']}")

                if "install_instructions" in tool_info:
                    print(f"   安装说明:")
                    for instruction in tool_info["install_instructions"]:
                        print(f"      {instruction}")

                if "config_example" in tool_info:
                    print(f"   或在配置文件中指定路径:")
                    print(f"      {tool_info['config_example']}")

            print("\n" + "="*70)
            raise RuntimeError(f"请安装缺失的打包工具后重试")

    def _prepare_environment(self, rollback_manager: Optional[RollbackManager] = None):
        """
        准备构建环境.
        """
        stage = "环境准备"
        self.progress.start_stage(stage, "创建构建目录和临时文件")

        # 创建临时目录
        self.temp_dir = self.file_ops.create_temp_dir("unifypy_build_")
        self.progress.update_stage(
            stage, 20, f"创建临时目录: {self.temp_dir}", absolute=True
        )

        # 创建输出目录（带回滚跟踪）
        if rollback_manager:
            if not self.dist_dir.exists():
                rollback_manager.safe_create_dir(self.dist_dir)
            if not self.installer_dir.exists():
                rollback_manager.safe_create_dir(self.installer_dir)
        else:
            self.file_ops.ensure_dir(str(self.dist_dir))
            self.file_ops.ensure_dir(str(self.installer_dir))

        self.progress.update_stage(stage, 40, "创建输出目录", absolute=True)

        # 预生成多平台配置（如果需要）
        self._prepare_platform_configs()

        # 清理旧文件（如果需要）
        if self.args.clean:
            self.progress.update_stage(stage, 60, "清理旧的构建文件", absolute=True)

            if rollback_manager:
                # 使用回滚管理器安全删除
                for item in self.dist_dir.iterdir():
                    if item.is_file():
                        rollback_manager.safe_delete_file(item)
                    elif item.is_dir():
                        # 目录删除需要递归处理
                        self._safe_remove_dir(item, rollback_manager)

                for item in self.installer_dir.iterdir():
                    if item.is_file():
                        rollback_manager.safe_delete_file(item)
                    elif item.is_dir():
                        self._safe_remove_dir(item, rollback_manager)
            else:
                self.file_ops.remove_dir(str(self.dist_dir))
                self.file_ops.remove_dir(str(self.installer_dir))
                self.file_ops.ensure_dir(str(self.dist_dir))
                self.file_ops.ensure_dir(str(self.installer_dir))

        # 准备图标文件
        self._prepare_icon()
        self.progress.update_stage(stage, 80, "准备资源文件", absolute=True)

        self.progress.complete_stage(stage)

    def _prepare_icon(self):
        """
        准备图标文件.
        """
        icon_path = self.config.get("icon")
        if not icon_path:
            # 不使用图标，避免创建无效的ico文件
            self.config.merged_config.pop("icon", None)
            if "pyinstaller" in self.config.merged_config:
                self.config.merged_config["pyinstaller"].pop("icon", None)
            return
        
        # 使用 ConfigManager 的路径解析方法
        icon_full_path = self.config.resolve_path(icon_path)
        if not icon_full_path.exists():
            # 不使用图标，避免创建无效的ico文件
            self.config.merged_config.pop("icon", None)
            if "pyinstaller" in self.config.merged_config:
                self.config.merged_config["pyinstaller"].pop("icon", None)

    def _create_default_icon(self, output_path: str):
        """
        创建默认图标.
        """
        try:
            from PIL import Image, ImageDraw

            # 创建32x32的图标
            size = (32, 32)
            image = Image.new("RGBA", size, (70, 130, 180, 255))  # 钢蓝色
            draw = ImageDraw.Draw(image)

            # 绘制简单的应用图标
            draw.rectangle([4, 4, 28, 28], outline=(255, 255, 255, 255), width=2)
            draw.text((8, 10), "Py", fill=(255, 255, 255, 255))

            # 保存为ICO格式
            image.save(output_path, format="ICO", sizes=[(32, 32)])

        except ImportError:
            # 如果PIL不可用，创建一个空的ICO文件
            with open(output_path, "wb") as f:
                # 写入最小的有效ICO文件头
                f.write(b"\x00\x00\x01\x00\x01\x00\x20\x20\x00\x00\x01\x00\x08\x00")
                f.write(b"\x00\x00\x00\x00\x16\x00\x00\x00")
                f.write(b"\x00" * 1024)  # 空的图像数据

    def _safe_remove_dir(self, dir_path: Path, rollback_manager: RollbackManager):
        """
        安全递归删除目录.
        """
        for item in dir_path.iterdir():
            if item.is_file():
                rollback_manager.safe_delete_file(item)
            elif item.is_dir():
                self._safe_remove_dir(item, rollback_manager)

    def _build_executable(self, rollback_manager: Optional[RollbackManager] = None):
        """
        构建可执行文件.
        """
        stage = "PyInstaller打包"
        self.progress.start_stage(stage, "使用PyInstaller生成可执行文件")

        # 在 macOS 上自动生成 entitlements.plist（如果需要）
        if platform.system().lower() == "darwin":  # macOS
            self.progress.update_stage(stage, 5, "检查 macOS 权限配置")

            # 判断是否为开发版本（默认开启，适用于未签名应用）
            # 只有明确指定 --production 时才禁用开发模式
            production = getattr(self.args, "production", False)
            development = (
                not production
                or getattr(self.args, "development", False)
                or getattr(self.args, "debug", False)
            )

            # 更新配置以包含自动生成的 entitlements
            # 注意：传递原始配置以保持 platforms 结构
            updated_config = (
                self.pyinstaller_builder.update_config_with_auto_entitlements(
                    self.config.raw_config, self.project_dir, development
                )
            )

            # 如果配置有更新，将新的 pyinstaller 配置合并到现有配置中
            if updated_config != self.config.raw_config:
                # 只更新 pyinstaller 部分，保持其他配置不变
                if "pyinstaller" in updated_config:
                    if "pyinstaller" not in self.config.merged_config:
                        self.config.merged_config["pyinstaller"] = {}
                    self.config.merged_config["pyinstaller"].update(
                        updated_config["pyinstaller"]
                    )

        # 获取PyInstaller配置（可能包含新生成的entitlements路径）
        pyinstaller_config = self.config.get_pyinstaller_config()

        self.progress.update_stage(stage, 10, "构建PyInstaller命令", absolute=True)

        # 构建命令（传递项目目录用于图标处理）
        entry_script = str(self.project_dir / self.config.get("entry"))

        # 处理图标格式转换
        if "icon" in pyinstaller_config and pyinstaller_config["icon"]:
            pyinstaller_config = self.pyinstaller_builder._icon_platform(
                pyinstaller_config,
                self.project_dir,
            )

        command = self.pyinstaller_builder.build_command(
            pyinstaller_config, entry_script
        )

        # 调试：显示完整的 PyInstaller 命令
        if getattr(self.args, "verbose", False):
            print("\n🔍 PyInstaller 命令调试:")
            print(f"完整命令: {' '.join(command)}")

            # 检查关键参数
            if "--osx-bundle-identifier" in command:
                idx = command.index("--osx-bundle-identifier")
                if idx + 1 < len(command):
                    print(f"  Bundle ID: {command[idx + 1]}")

            if "--osx-entitlements-file" in command:
                idx = command.index("--osx-entitlements-file")
                if idx + 1 < len(command):
                    entitlements_path = command[idx + 1]
                    print(f"  Entitlements: {entitlements_path}")
                    print(f"  文件存在: {Path(entitlements_path).exists()}")

            print()

        # 设置工作目录
        original_cwd = os.getcwd()
        os.chdir(str(self.project_dir))

        try:
            self.progress.update_stage(stage, 20, "执行PyInstaller打包", absolute=True)

            # 执行PyInstaller
            success = self.runner.run_command(
                command,
                stage,
                "正在打包Python应用...",
                60,
                capture_output=not self.args.verbose,
                shell=False,
            )

            if not success:
                raise RuntimeError("PyInstaller打包失败")

            self.progress.update_stage(stage, 90, "验证输出文件", absolute=True)

            # 验证输出
            app_name = self.config.get("name")
            if self.config.get_pyinstaller_config().get("onefile"):
                exe_path = (
                    self.dist_dir
                    / f"{app_name}{self.file_ops.get_executable_extension()}"
                )
            else:
                exe_path = (
                    self.dist_dir
                    / app_name
                    / f"{app_name}{self.file_ops.get_executable_extension()}"
                )

            if not exe_path.exists():
                raise RuntimeError(f"PyInstaller输出文件不存在: {exe_path}")

            # 在 macOS 上更新 Info.plist 权限描述
            if platform.system().lower() == "darwin":
                self._update_macos_info_plist(app_name)

            self.progress.complete_stage(stage)

        finally:
            os.chdir(original_cwd)

    def _update_macos_info_plist(self, app_name: str):
        """
        更新 macOS .app 包中的 Info.plist 权限描述.
        """
        try:
            # 查找 .app 包
            app_path = self.dist_dir / f"{app_name}.app"

            if not app_path.exists():
                print(f"⚠️ 未找到 .app 包: {app_path}")
                return

            # 获取 macOS 配置
            macos_config = self.config._get_platform_config().get("macos", {})
            if not macos_config:
                # 从原始配置获取
                raw_config = getattr(self.config, "raw_config", {})
                if "platforms" in raw_config:
                    macos_config = raw_config["platforms"].get("macos", {})

            if not macos_config:
                print("⚠️ 未找到 macOS 平台配置")
                return

            if self.args.verbose:
                print("🔧 更新 macOS 权限描述...")

            success = self.info_plist_updater.update_app_info_plist(
                app_path, macos_config
            )

            if success:
                if self.args.verbose:
                    print("✅ Info.plist 权限描述更新完成")

                    # 显示已添加的权限
                    permissions = self.info_plist_updater.list_app_permissions(app_path)
                    if permissions:
                        print("📋 已配置的权限描述:")
                        for key, desc in permissions.items():
                            print(f"  • {key}: {desc[:60]}...")

                # 关键步骤：执行 ad-hoc 代码签名以应用 entitlements
                self._sign_macos_app(app_path)

            else:
                print("⚠️ Info.plist 权限描述更新失败")  # 错误信息始终显示

        except Exception as e:
            print(f"❌ Info.plist 更新异常: {e}")

    def _sign_macos_app(self, app_path: Path):
        """
        对 macOS .app 包执行 ad-hoc 代码签名以应用 entitlements.
        """
        try:
            if self.args.verbose:
                print(f"🔐 准备对 {app_path.name} 执行代码签名...")

            # 检查 codesign 工具是否可用
            if not self.macos_codesigner.check_codesign_available():
                print("⚠️ codesign 工具不可用，跳过代码签名")  # 错误信息始终显示
                return

            # 查找 entitlements.plist 文件
            entitlements_path = None

            # 首先检查项目根目录
            project_entitlements = self.project_dir / "entitlements.plist"
            if project_entitlements.exists():
                entitlements_path = project_entitlements
                if self.args.verbose:
                    print(f"📜 找到 entitlements 文件: {entitlements_path}")

            # 如果没找到，检查 .app 包内的 entitlements
            if not entitlements_path:
                app_entitlements = app_path / "Contents" / "entitlements.plist"
                if app_entitlements.exists():
                    entitlements_path = app_entitlements
                    if self.args.verbose:
                        print(
                            f"📜 使用 .app 包内的 entitlements: " f"{entitlements_path}"
                        )

            # 执行签名
            success = self.macos_codesigner.sign_app_with_entitlements(
                app_path, entitlements_path
            )

            if success:
                if self.args.verbose:
                    print("✅ macOS 代码签名完成，权限应该已生效")
            else:
                print("⚠️ 代码签名失败，但应用仍可正常使用")  # 警告信息始终显示

        except Exception as e:
            print(f"❌ macOS 代码签名异常: {e}")

    def _build_installer(self, rollback_manager: Optional[RollbackManager] = None):
        """
        构建安装包.
        """
        stage = "安装包生成"
        self.progress.start_stage(stage, "生成平台特定的安装包")

        platform = self.config.current_platform

        # 获取要生成的格式列表
        requested_formats = self._get_requested_formats(platform)

        if not requested_formats:
            self.progress.warning(f"未指定 {platform} 平台的输出格式")
            self.progress.complete_stage(stage)
            return

        # 确定源文件路径
        app_name = self.config.get("name")
        if self.config.get_pyinstaller_config().get("onefile"):
            source_path = self.dist_dir / (
                f"{app_name}{self.file_ops.get_executable_extension()}"
            )
        else:
            source_path = self.dist_dir / app_name

        # 检查是否启用并行构建
        if self.args.parallel and len(requested_formats) > 1:
            success_count = self._build_parallel_installers(
                platform, requested_formats, source_path
            )
            total_formats = len(requested_formats)
        else:
            # 为每种格式生成安装包（串行）
            success_count = 0
            total_formats = len(requested_formats)

            for i, format_type in enumerate(requested_formats):
                format_progress = int(80 * (i + 1) / total_formats)

                success = self._build_platform_installer(
                    platform, format_type, source_path, format_progress
                )

                if success:
                    success_count += 1

        if success_count == 0:
            self.progress.on_error(Exception("所有格式的安装包生成都失败了"), stage)
        elif success_count < total_formats:
            self.progress.warning(
                f"部分安装包生成失败 ({success_count}/{total_formats} 成功)"
            )

        self.progress.complete_stage(stage)

    def _get_requested_formats(self, platform: str) -> List[str]:
        """
        获取请求的输出格式列表.
        """
        # 如果命令行指定了格式，使用指定的格式
        if self.args.format:
            return [self.args.format]

        # 从配置中获取格式
        platform_config = self.config.get("platforms", {}).get(platform, {})

        # 获取所有配置的格式
        formats = []
        for key in platform_config.keys():
            if self.packager_registry.is_format_supported(platform, key):
                formats.append(key)

        # 如果没有配置格式，使用默认格式
        if not formats:
            default_formats = {
                "windows": ["exe"],
                "macos": ["dmg"],
                "linux": ["tar.gz"],
            }
            formats = default_formats.get(platform, [])

        return formats

    def _build_platform_installer(
        self,
        platform: str,
        format_type: str,
        source_path: Path,
        progress_weight: int,
    ) -> bool:
        """
        构建特定平台和格式的安装包.
        """
        # 获取打包器类
        packager_class = self.packager_registry.get_packager(platform, format_type)
        if not packager_class:
            self.progress.warning(f"未找到 {platform}/{format_type} 格式的打包器")
            return False

        # 预处理配置中的路径
        processed_config = self._preprocess_config_paths(self.config.merged_config)
        
        # 创建打包器实例
        packager = packager_class(
            self.progress,
            self.runner,
            self.tool_manager,
            processed_config,
        )

        # 验证配置
        errors = packager.validate_config(format_type)
        if errors:
            self.progress.warning(f"{format_type}格式配置验证失败:")
            for error in errors:
                self.progress.warning(f"  - {error}")

        # 生成输出文件名
        app_name = self.config.get("name")
        version = self.config.get("version")
        output_filename = packager.get_output_filename(format_type, app_name, version)
        output_path = self.installer_dir / output_filename

        self.progress.update_stage(
            "安装包生成", 0, f"正在生成 {format_type.upper()} 格式安装包..."
        )

        # 执行打包
        try:
            success = packager.package(format_type, source_path, output_path)

            if success:
                self.progress.update_stage("安装包生成", progress_weight)
                self.progress.info(
                    f"✅ {format_type.upper()} 安装包已生成: {output_path}"
                )
                return True
            else:
                self.progress.warning(f"❌ {format_type.upper()} 安装包生成失败")
                return False

        except Exception as e:
            self.progress.on_error(
                Exception(f"{format_type.upper()} 打包失败: {e}"), "安装包生成"
            )
            return False

    def _build_parallel_installers(
        self, platform: str, formats: List[str], source_path: Path
    ) -> int:
        """
        使用并行构建生成多种格式的安装包.
        """
        try:
            with ParallelBuilder(
                self.progress, self.args.max_workers
            ) as parallel_builder:
                # 优化PyInstaller构建配置
                pyinstaller_config = self.config.get_pyinstaller_config()
                parallel_builder.optimize_pyinstaller_build(
                    pyinstaller_config,
                    str(self.project_dir / self.config.get("entry")),
                    self.project_dir,
                )

                # 预处理配置中的路径
                processed_config = self._preprocess_config_paths(self.config.merged_config)
                
                # 并行构建多种格式
                results = parallel_builder.build_multiple_formats(
                    platform,
                    formats,
                    self.packager_registry,
                    source_path,
                    self.installer_dir,
                    processed_config,
                )

                # 统计成功数量
                success_count = sum(1 for success in results.values() if success)

                # 显示详细结果
                for format_type, success in results.items():
                    status = "✅ 成功" if success else "❌ 失败"
                    self.progress.info(f"{format_type.upper()}: {status}")

                return success_count

        except Exception as e:
            self.progress.on_error(Exception(f"并行构建失败: {e}"), "安装包生成")
            return 0

    def _preprocess_config_paths(self, config: dict) -> dict:
        """
        预处理配置中的文件路径，将相对路径转换为绝对路径.
        
        Args:
            config: 原始配置字典
            
        Returns:
            dict: 处理后的配置字典
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
        for field in array_path_fields:
            if field in processed_config and processed_config[field]:
                processed_list = []
                for item in processed_config[field]:
                    if isinstance(item, str):
                        # 处理 "source:dest" 格式
                        if ":" in item or ";" in item:
                            separator = ":" if ":" in item else ";"
                            parts = item.split(separator, 1)
                            if len(parts) == 2:
                                source, dest = parts
                                if not os.path.isabs(source):
                                    source = str(self.project_dir / source)
                                processed_list.append(f"{source}{separator}{dest}")
                            else:
                                processed_list.append(item)
                        else:
                            # 单个路径
                            if not os.path.isabs(item):
                                item = str(self.project_dir / item)
                            processed_list.append(item)
                    else:
                        processed_list.append(item)
                processed_config[field] = processed_list
        
        # 处理嵌套配置中的路径（如平台特定配置）
        for platform_key in ["windows", "macos", "linux", "platforms"]:
            if platform_key in processed_config:
                platform_config = processed_config[platform_key]
                if isinstance(platform_config, dict):
                    self._process_nested_paths(platform_config)
        
        # 处理 PyInstaller 配置中的路径
        if "pyinstaller" in processed_config:
            pyinstaller_config = processed_config["pyinstaller"]
            if isinstance(pyinstaller_config, dict):
                self._process_nested_paths(pyinstaller_config)
        
        return processed_config
    
    def _process_nested_paths(self, config: dict):
        """
        递归处理嵌套配置中的文件路径.
        
        Args:
            config: 配置字典
        """
        path_fields = [
            "icon", "license", "readme", "entry",
            "setup_icon", "license_file", "readme_file", 
            "volicon", "version_file", "manifest"
        ]
        
        array_path_fields = ["add_data", "add_binary", "datas", "binaries"]
        
        # 处理单个路径字段
        for field in path_fields:
            if field in config and config[field]:
                path = config[field]
                if isinstance(path, str) and not os.path.isabs(path):
                    config[field] = str(self.project_dir / path)
        
        # 处理数组路径字段
        for field in array_path_fields:
            if field in config and config[field]:
                processed_list = []
                for item in config[field]:
                    if isinstance(item, str):
                        # 处理 "source:dest" 格式
                        if ":" in item or ";" in item:
                            separator = ":" if ":" in item else ";"
                            parts = item.split(separator, 1)
                            if len(parts) == 2:
                                source, dest = parts
                                if not os.path.isabs(source):
                                    source = str(self.project_dir / source)
                                processed_list.append(f"{source}{separator}{dest}")
                            else:
                                processed_list.append(item)
                        else:
                            # 单个路径
                            if not os.path.isabs(item):
                                item = str(self.project_dir / item)
                            processed_list.append(item)
                    else:
                        processed_list.append(item)
                config[field] = processed_list
        
        # 递归处理嵌套字典
        for key, value in config.items():
            if isinstance(value, dict):
                self._process_nested_paths(value)

    def _prepare_platform_configs(self):
        """
        预生成多平台配置文件
        """
        try:
            # 初始化缓存管理器
            cache_manager = CacheManager(str(self.project_dir))
            
            # 检查是否需要预生成配置
            should_pre_generate = cache_manager.should_pre_generate_all_configs(self.config.merged_config)
            if should_pre_generate:
                self.progress.update_stage("环境准备", 45, "预生成多平台配置...", absolute=True)
                
                # 执行多平台配置预生成
                results = cache_manager.pre_generate_all_platform_configs(
                    self.config.merged_config, 
                    self.config.config_path if hasattr(self.config, 'config_path') else None
                )
                
                # 统计生成结果
                success_count = sum(1 for result in results.values() if result is True)
                total_count = len([p for p in results.keys() if results[p] != "skipped"])
                
                if success_count > 0:
                    self.progress.info(f"✅ 预生成 {success_count}/{total_count} 个平台配置")
                else:
                    self.progress.info("📋 使用现有缓存配置")
            else:
                self.progress.update_stage("环境准备", 45, "使用缓存配置", absolute=True)
                self.progress.info("📋 使用现有缓存配置")
                
        except Exception as e:
            # 配置预生成失败不应阻止主流程
            self.progress.warning(f"配置预生成失败: {e}")

    def _show_success(self):
        """
        显示成功信息.
        """
        # 收集输出文件信息
        output_info = {}

        app_name = self.config.get("name")

        # 可执行文件
        if not self.args.skip_exe:
            if self.config.get_pyinstaller_config().get("onefile"):
                exe_path = (
                    self.dist_dir
                    / f"{app_name}{self.file_ops.get_executable_extension()}"
                )
            else:
                exe_path = self.dist_dir / app_name

            if exe_path.exists():
                output_info["可执行文件"] = str(exe_path)

        # 安装包（检查所有生成的文件）
        if not self.args.skip_installer and self.installer_dir.exists():
            installer_files = []
            for file_path in self.installer_dir.iterdir():
                if file_path.is_file():
                    installer_files.append(str(file_path))

            if installer_files:
                if len(installer_files) == 1:
                    output_info["安装包"] = installer_files[0]
                else:
                    output_info["安装包"] = installer_files

        self.progress.show_success(output_info)

    def _cleanup(self):
        """
        清理临时文件.
        """
        if self.temp_dir:
            self.file_ops.cleanup_temp_dir(self.temp_dir)

    def _list_rollback_sessions(self) -> int:
        """
        列出可用的回滚会话.
        """
        rollback_manager = RollbackManager(self.project_dir, self.progress)
        sessions = rollback_manager.list_rollback_sessions()

        if not sessions:
            print("没有可用的回滚会话")
            return 0

        print("可用的回滚会话:")
        print("-" * 60)

        for session_id in sessions:
            session_info = rollback_manager.get_session_info(session_id)
            if session_info:
                import datetime

                start_time = datetime.datetime.fromtimestamp(session_info["start_time"])
                print(f"会话ID: {session_id}")
                print(f"  时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  操作数: {session_info['operation_count']}")
                print(f"  回滚命令: python main.py . --rollback {session_id}")
                print()

        return 0

    def _execute_rollback(self, session_id: str) -> int:
        """
        执行指定会话的回滚.
        """
        rollback_manager = RollbackManager(self.project_dir, self.progress)

        if not rollback_manager.load_operations(session_id):
            print(f"错误: 会话 {session_id} 不存在或无法加载")
            return 1

        print(f"正在回滚会话: {session_id}")
        success = rollback_manager.rollback()

        if success:
            print("✅ 回滚成功完成")
            rollback_manager.cleanup()
            return 0
        else:
            print("❌ 回滚过程中发生错误")
            return 1


def main():
    """
    主函数.
    """
    args = parse_arguments()

    # 创建构建器并运行
    builder = UnifyPyBuilder(args)
    return builder.run()


if __name__ == "__main__":
    sys.exit(main())
