#!/usr/bin/env python
# -*- coding: utf-8-sig -*-
"""
多平台打包工厂
为Windows、MacOS和Linux提供特定的打包实现
"""

import os
import sys
import shutil
import platform
import subprocess
import abc
from typing import Dict, Any
import tempfile
import glob
import datetime


class PlatformPackager(abc.ABC):
    """平台打包器抽象基类"""

    def __init__(self, env: Dict[str, Any]):
        """
        初始化平台打包器

        Args:
            env: 打包环境信息和配置
        """
        self.env = env
        self.platform_config = env.get("platform_config", {})

    @abc.abstractmethod
    def prepare_environment(self) -> bool:
        """准备打包环境"""
        pass

    @abc.abstractmethod
    def build_executable(self) -> bool:
        """构建可执行文件"""
        pass

    @abc.abstractmethod
    def build_installer(self) -> bool:
        """构建安装程序"""
        pass

    @abc.abstractmethod
    def verify_output(self) -> bool:
        """验证输出文件"""
        pass

    def run_command(self, command, description, shell=True) -> bool:
        """运行系统命令"""
        print(f"\n{'='*60}")
        print(f"步骤: {description}")
        print(f"{'='*60}")

        # 根据命令类型显示不同格式的命令信息
        if isinstance(command, list):
            print(f"执行命令: {' '.join(str(item) for item in command)}")
        else:
            print(f"执行命令: {command}")

        try:
            result = subprocess.run(command, shell=shell)

            if result.returncode == 0:
                print(f"\n✓ {description}完成！")
                return True
            else:
                print(f"\n❌ {description}失败！")
                return False
        except Exception as e:
            print(f"\n❌ {description}失败: {e}")
            return False

    def get_executable_name(self) -> str:
        """获取可执行文件名称"""
        return self.env["app_name"]


class WindowsPackager(PlatformPackager):
    """Windows平台打包实现"""

    def prepare_environment(self) -> bool:
        """准备Windows平台打包环境"""
        print("准备Windows平台打包环境...")

        # 复制Inno Setup模板文件
        setup_iss_template = os.path.join(
            self.env["templates_dir"], "setup.iss.template")
        setup_iss_path = os.path.join(self.env["temp_dir"], "setup.iss")

        if not os.path.exists(setup_iss_template):
            print(f"错误: 找不到Inno Setup模板文件: {setup_iss_template}")
            return False

        # 读取模板内容
        with open(setup_iss_template, 'r', encoding='utf-8-sig') as f:
            template_content = f.read()

        # 替换模板变量
        template_content = template_content.replace(
            "{{APP_NAME}}", self.env["app_name"])
        template_content = template_content.replace(
            "{{APP_VERSION}}", self.env["version"])
        template_content = template_content.replace(
            "{{APP_PUBLISHER}}", self.env["publisher"])
        template_content = template_content.replace(
            "{{DISPLAY_NAME}}", self.env["display_name"])

        # 注意：installer_options中的languages设置由模板自身处理

        # 添加dist目录和installer目录的绝对路径
        if self.env.get("onefile", False):
            # 单文件模式，可执行文件直接位于dist目录
            source_path = os.path.abspath(
                os.path.join(self.env["project_dir"], "dist"))
        else:
            # 目录模式，可执行文件位于dist/app_name目录下
            source_path = os.path.abspath(
                os.path.join(
                    self.env["project_dir"],
                    "dist",
                    self.env["app_name"]))

        template_content = template_content.replace(
            "{{SOURCE_PATH}}", source_path)

        output_path = os.path.abspath(
            os.path.join(
                self.env["project_dir"],
                "installer"))
        template_content = template_content.replace(
            "{{OUTPUT_PATH}}", output_path)

        # 写入处理后的模板
        with open(setup_iss_path, 'w', encoding='utf-8-sig') as f:
            f.write(template_content)

        return True

    def build_executable(self) -> bool:
        """构建Windows可执行文件"""
        print("构建Windows可执行文件...")

        # 修改额外参数以适应Windows特性
        additional_args = self.platform_config.get(
            "additional_pyinstaller_args", "")
        if not additional_args:
            additional_args = self.env.get("additional_args", "")

        # 构建命令
        build_cmd = [
            sys.executable,
            os.path.join(self.env["temp_dir"], "build_exe.py"),
            "--name", self.env["app_name"],
            "--entry", self.env["entry_file"]
        ]

        # 添加钩子目录参数
        if self.env.get("hooks_dir"):
            build_cmd.extend(["--hooks", self.env["hooks_dir"]])

        # 添加单文件模式参数(如果启用)
        if self.env.get("onefile", False):
            build_cmd.append("--onefile")
            print("使用单文件模式打包")
        else:
            print("使用目录模式打包，资源文件将与可执行文件处于同一级目录")

        # 添加额外的PyInstaller参数
        if additional_args:
            # 将额外参数用引号包装，作为一个整体传递
            additional_args = additional_args.replace('"', '\\"')  # 转义引号
            build_cmd.extend(["--additional", f'"{additional_args}"'])
            print(f"添加额外PyInstaller参数: {additional_args}")

        # 执行构建
        return self.run_command(build_cmd, "构建Windows可执行文件")

    def build_installer(self) -> bool:
        """构建Windows安装程序"""
        if self.env.get("skip_installer", False):
            print("跳过Windows安装程序构建步骤")
            return True

        print("构建Windows安装程序...")

        # 构建命令
        installer_cmd = [
            sys.executable,
            os.path.join(self.env["temp_dir"], "build_installer.py"),
            "--name", self.env["app_name"],
            "--iss", os.path.join(self.env["temp_dir"], "setup.iss")
        ]

        # 添加Inno Setup路径参数（如果有）
        if self.env.get("inno_setup_path"):
            # 确保路径被引号包裹，防止空格引起的问题
            inno_path = self.env["inno_setup_path"].strip('"')  # 去除可能已有的引号
            installer_cmd.extend(["--inno-path", f'"{inno_path}"'])
            print(f"使用Inno Setup路径: {inno_path}")

        # 执行构建 - 使用列表形式的命令而不是字符串，以避免命令行参数解析的问题
        result = self.run_command(installer_cmd, "构建Windows安装程序", shell=False)

        # 如果失败，提供更友好的错误提示
        if not result:
            print("\n注意: Windows安装程序构建需要Inno Setup，请按照提示安装后重试")
            print("可以在config.json文件中通过'inno_setup_path'参数指定Inno Setup路径")
            print("或者在命令行使用'--inno-setup-path'参数指定路径")

        return result

    def verify_output(self) -> bool:
        """验证Windows输出文件"""
        # 检查可执行文件是否存在
        if self.env.get("onefile", False):
            # 单文件模式，可执行文件直接位于dist目录
            exe_path = os.path.join(
                self.env["project_dir"], "dist", f"{self.env['app_name']}.exe")
        else:
            # 目录模式，可执行文件位于dist/app_name目录下
            exe_path = os.path.join(
                self.env["project_dir"], "dist", self.env['app_name'],
                f"{self.env['app_name']}.exe")

        if not os.path.exists(exe_path):
            print(f"❌ 找不到Windows可执行文件: {exe_path}")
            return False

        print(f"已确认Windows可执行文件存在: {exe_path}")
        print(f"文件大小: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")
        return True


class MacOSPackager(PlatformPackager):
    """MacOS平台打包实现"""

    def prepare_environment(self) -> bool:
        """准备MacOS平台打包环境"""
        print("准备MacOS平台打包环境...")

        # 检查是否安装了create-dmg（用于创建DMG安装包）
        try:
            subprocess.run(['which', 'create-dmg'], check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("✓ 检测到create-dmg已安装")
        except subprocess.CalledProcessError:
            print("⚠️ 未检测到create-dmg，将无法创建DMG安装包")
            print("  提示: 可以通过Homebrew安装: brew install create-dmg")

        # 即使工具未安装也不影响环境准备，因为可以构建.app包
        return True

    def build_executable(self) -> bool:
        """构建MacOS可执行文件"""
        print("构建MacOS可执行文件...")

        # 获取MacOS特定配置
        additional_args = self.platform_config.get(
            "additional_pyinstaller_args", "")
        if not additional_args:
            additional_args = self.env.get("additional_args", "")

        # MacOS特定配置，确保使用:代替;作为路径分隔符
        additional_args = additional_args.replace(";", ":")

        # 构建命令
        build_cmd = [
            sys.executable,
            os.path.join(self.env["temp_dir"], "build_exe.py"),
            "--name", self.env["app_name"],
            "--entry", self.env["entry_file"]
        ]

        # 添加钩子目录参数
        if self.env.get("hooks_dir"):
            build_cmd.extend(["--hooks", self.env["hooks_dir"]])

        # 添加单文件模式参数(如果启用)
        if self.env.get("onefile", False):
            build_cmd.append("--onefile")
            print("使用单文件模式打包")
        else:
            print("使用目录模式打包，资源文件将与可执行文件处于同一级目录")

        # 添加额外的PyInstaller参数
        if additional_args:
            # 将额外参数用引号包装，作为一个整体传递
            additional_args = additional_args.replace('"', '\\"')  # 转义引号
            build_cmd.extend(["--additional", f'"{additional_args}"'])
            print(f"添加额外PyInstaller参数: {additional_args}")

        # 执行构建
        return self.run_command(build_cmd, "构建MacOS可执行文件")

    def build_installer(self) -> bool:
        """构建MacOS安装程序（DMG文件）"""
        if self.env.get("skip_installer", False):
            print("跳过MacOS安装程序构建步骤")
            return True

        print("构建MacOS DMG安装镜像...")

        # 检查create-dmg是否可用
        try:
            subprocess.run(["which", "create-dmg"],
                           check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("错误: 未安装create-dmg，无法创建DMG安装镜像")
            print("请使用以下方式安装create-dmg:")
            print("- 使用Homebrew安装: brew install create-dmg")
            print("- 或访问: https://github.com/create-dmg/create-dmg 获取其他安装方式")
            return False

        # 确定app位置
        app_path = None
        app_name = None

        if self.env.get("onefile", False):
            # 单文件模式，可执行文件直接位于dist目录
            app_path = os.path.join(self.env["project_dir"], "dist")
            app_name = self.env["app_name"]
            print(f"使用单文件模式，从目录构建DMG: {app_path}")
        else:
            # 目录模式，应用程序包位于dist目录下
            app_name = self.platform_config.get(
                "app_bundle_name", f"{self.env['app_name']}.app")

            # 检查可能的路径
            possible_paths = [
                os.path.join(self.env["project_dir"], "dist", app_name),
                os.path.join(self.env["project_dir"],
                             "dist", self.env["app_name"], app_name),
                os.path.join(self.env["project_dir"],
                             "dist", self.env["app_name"])
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    app_path = path
                    print(f"找到应用程序位置: {app_path}")
                    break

            if not app_path:
                print("错误: 无法找到macOS应用程序包，已尝试以下路径:")
                for path in possible_paths:
                    print(f"- {path}")
                return False

        # 创建DMG输出目录
        installer_dir = self.env["installer_dir"]
        os.makedirs(installer_dir, exist_ok=True)

        # 创建DMG文件
        dmg_file = os.path.join(
            installer_dir,
            f"{self.env['app_name']}-{self.env['version']}.dmg")

        # 构建DMG创建命令 - 使用字符串列表避免路径中空格问题
        dmg_cmd = [
            "create-dmg",
            "--volname", f"{self.env['display_name']} Installer",
            "--window-pos", "200", "100",
            "--window-size", "800", "400",
            "--icon-size", "100",
            "--app-drop-link", "600", "185",
            dmg_file,
            app_path
        ]

        # 执行DMG创建
        print(f"执行命令: {' '.join(dmg_cmd)}")
        try:
            result = subprocess.run(dmg_cmd, check=False)
            if result.returncode == 0:
                print("✓ 创建MacOS DMG安装镜像成功")
                return True
            else:
                print(f"❌ 创建DMG失败，返回码: {result.returncode}")
                return False
        except Exception as e:
            print(f"❌ 执行命令失败: {e}")
            return False

    def verify_output(self) -> bool:
        """验证macOS打包输出结果，检查.app和.dmg文件是否存在及其完整性"""
        print("\n开始验证macOS打包结果...")

        output_dir = os.path.join(self.env["project_dir"], 'dist')
        app_name = self.env["app_name"]
        app_bundle = f"{app_name}.app"
        app_dir = os.path.join(output_dir, app_bundle)

        # 检查.app包是否存在
        if not os.path.exists(app_dir):
            print("❌ 错误: .app应用包不存在")
            return False

        # 检查可执行文件
        exe_path = os.path.join(app_dir, "Contents/MacOS", app_name)
        if not os.path.exists(exe_path):
            print("⚠️ 警告: 主可执行文件不存在")

            # 尝试查找替代的可执行文件
            macos_dir = os.path.join(app_dir, "Contents/MacOS")
            if os.path.exists(macos_dir):
                exe_files = [f for f in os.listdir(
                    macos_dir) if os.path.isfile(os.path.join(macos_dir, f))]
                if exe_files:
                    print("  找到替代可执行文件:")
                    for exe in exe_files:
                        exe_path = os.path.join(macos_dir, exe)
                        print(f"  - {exe}")
                        size_kb = os.path.getsize(exe_path) / 1024
                        if size_kb < 1024:
                            print(f"    大小: {size_kb:.2f} KB")
                        else:
                            size_mb = size_kb / 1024
                            print(f"    大小: {size_mb:.2f} MB")
                    # 使用第一个找到的可执行文件继续验证
                    exe_path = os.path.join(macos_dir, exe_files[0])
                else:
                    print("❌ 错误: 找不到任何可执行文件")
                    return False
            else:
                print("❌ 错误: MacOS目录不存在")
                return False

        # 检查可执行文件权限
        exe_stat = os.stat(exe_path)
        if exe_stat.st_mode & 0o111:  # 检查是否有执行权限
            print("✓ 可执行文件权限正确")
        else:
            print("⚠️ 警告: 可执行文件缺少执行权限，尝试修复...")
            os.chmod(exe_path, 0o755)

        # 显示可执行文件大小
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"✓ 可执行文件大小: {size_mb:.2f} MB")

        # 检查Info.plist
        info_plist = os.path.join(app_dir, "Contents/Info.plist")
        if os.path.exists(info_plist):
            print("✓ Info.plist 存在")

            # 尝试检查Info.plist内容
            try:
                with open(info_plist, 'rb') as f:
                    import plistlib
                    info = plistlib.load(f)

                    bundle_id = info.get('CFBundleIdentifier')
                    bundle_name = info.get('CFBundleName')
                    bundle_version = info.get('CFBundleShortVersionString')

                    print(f"  - 应用标识符: {bundle_id or '未设置'}")
                    print(f"  - 应用名称: {bundle_name or '未设置'}")
                    print(f"  - 应用版本: {bundle_version or '未设置'}")

                    # 检查关键设置
                    if not bundle_id:
                        print("⚠️ 警告: 未设置应用标识符 (CFBundleIdentifier)")
                    if not bundle_version:
                        print("⚠️ 警告: 未设置应用版本 (CFBundleShortVersionString)")
            except Exception as e:
                print(f"⚠️ 无法解析Info.plist内容: {e}")
        else:
            print("❌ 错误: Info.plist 不存在")

        # 检查图标文件
        icon_path = os.path.join(
            app_dir, "Contents/Resources", f"{app_name}.icns")
        if os.path.exists(icon_path):
            print("✓ 应用图标存在")
            icon_size_kb = os.path.getsize(icon_path) / 1024
            print(f"  - 图标大小: {icon_size_kb:.2f} KB")
        elif self.platform_config.get("icon"):
            print("⚠️ 警告: 未找到指定的应用图标")
            resources_dir = os.path.join(app_dir, "Contents/Resources")
            icns_files = [f for f in os.listdir(
                resources_dir) if f.endswith('.icns')]
            if icns_files:
                print("  找到其他图标文件:")
                for icon in icns_files:
                    print(f"  - {icon}")
                print("  - 可能应用了默认图标或图标名称与应用名称不匹配")
        else:
            print("ℹ️ 未配置自定义图标，应用使用默认图标")

        # 验证DMG文件（如果不跳过安装程序）
        if not self.env.get("skip_installer", False):
            dmg_name = f"{app_name}-{self.env['version']}.dmg"
            dmg_path = os.path.join(output_dir, dmg_name)

            if os.path.exists(dmg_path):
                print("✓ DMG安装包创建成功")

                # 显示DMG大小
                size_mb = os.path.getsize(dmg_path) / (1024 * 1024)
                print(f"  - {os.path.basename(dmg_path)} ({size_mb:.2f} MB)")

                # 检查DMG签名
                print("  验证DMG签名:")
                try:
                    result = subprocess.run(
                        ['codesign', '-v', dmg_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=False
                    )
                    if result.returncode == 0:
                        print("✓ DMG签名验证通过")
                    else:
                        print("ℹ️ DMG未签名或签名无效")
                except Exception as e:
                    print(f"ℹ️ 无法验证DMG签名: {e}")

                print("  提示: 可以使用以下命令挂载DMG: ")
                print(f"  hdiutil attach \"{dmg_path}\"")
            else:
                print("❌ 错误: DMG安装包不存在")
        else:
            print("ℹ 跳过DMG验证，因为设置了skip_installer=True")

        print("\n✓ macOS打包验证完成 ✓")
        return True


class LinuxPackager(PlatformPackager):
    """Linux平台打包实现"""

    def prepare_environment(self) -> bool:
        """准备Linux平台打包环境"""
        print("准备Linux平台打包环境...")

        # 获取目标打包格式
        target_format = self.platform_config.get("format", "appimage").lower()
        required_tools = []

        # 根据目标格式确定必需工具
        if target_format == "appimage":
            required_tools.append("appimagetool")
        elif target_format == "deb":
            required_tools.append("dpkg-deb")
        elif target_format == "rpm":
            required_tools.append("rpmbuild")

        # 检查是否安装了必要的工具
        missing_tools = []
        for tool in required_tools:
            try:
                subprocess.run(["which", tool], check=True,
                               capture_output=True)
                print(f"✓ 已找到 {tool}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)
                print(f"❌ 未找到 {tool}，此工具对于创建 {target_format} 格式安装包是必需的")

        # 如果有缺失的必要工具，提供安装建议
        if missing_tools:
            print("\n以下工具未安装，请安装后再试:")
            if "appimagetool" in missing_tools:
                print(
                    "- appimagetool: 请访问 https://github.com/AppImage/AppImageKit/releases 下载")
                print("  或使用以下命令安装: ")
                print(
                    "  wget -c https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage")
                print("  chmod +x appimagetool-x86_64.AppImage")
                print(
                    "  sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool")
            if "dpkg-deb" in missing_tools:
                print("- dpkg-deb: 使用 sudo apt-get install dpkg-dev 安装")
            if "rpmbuild" in missing_tools:
                print(
                    "- rpmbuild: 使用 sudo dnf install rpm-build (Fedora) 或 sudo yum install rpm-build (CentOS) 安装")

            # 如果缺失的是目标格式所需的必要工具，则返回失败
            if set(missing_tools).intersection(set(required_tools)):
                print(f"\n❌ 缺少创建 {target_format} 格式安装包所需的工具，无法继续")
                return False

        return True

    def build_executable(self) -> bool:
        """构建Linux可执行文件"""
        print("构建Linux可执行文件...")

        # 获取Linux特定配置
        additional_args = self.platform_config.get(
            "additional_pyinstaller_args", "")
        if not additional_args:
            additional_args = self.env.get("additional_args", "")

        # Linux特定配置，确保使用:代替;作为路径分隔符
        additional_args = additional_args.replace(";", ":")

        # 构建命令
        build_cmd = [
            sys.executable,
            os.path.join(self.env["temp_dir"], "build_exe.py"),
            "--name", self.env["app_name"],
            "--entry", self.env["entry_file"]
        ]

        # 添加钩子目录参数
        if self.env.get("hooks_dir"):
            build_cmd.extend(["--hooks", self.env["hooks_dir"]])

        # 添加单文件模式参数(如果启用)
        if self.env.get("onefile", False):
            build_cmd.append("--onefile")
            print("使用单文件模式打包")
        else:
            print("使用目录模式打包，资源文件将与可执行文件处于同一级目录")

        # 添加额外的PyInstaller参数
        if additional_args:
            # Linux平台不需要用额外引号包装参数，直接传递即可
            build_cmd.extend(["--additional", additional_args])
            print(f"添加额外PyInstaller参数: {additional_args}")

        # 执行构建 - 对于Linux使用shell=False更安全
        return self.run_command(build_cmd, "构建Linux可执行文件", shell=False)

    def build_installer(self) -> bool:
        """构建Linux安装包（AppImage或deb/rpm包）"""
        if self.env.get("skip_installer", False):
            print("跳过Linux安装程序构建步骤")
            return True

        # 获取格式配置
        install_format = self.platform_config.get("format", "appimage").lower()
        print(f"准备构建Linux {install_format} 格式安装包...")

        # 检查可执行文件位置
        if self.env.get("onefile", False):
            # 单文件模式，可执行文件直接位于dist目录
            exe_dir = os.path.join(self.env["project_dir"], "dist")
            exe_path = os.path.join(exe_dir, self.env["app_name"])
        else:
            # 目录模式，可执行文件位于dist/app_name目录下
            exe_dir = os.path.join(
                self.env["project_dir"], "dist", self.env["app_name"])
            exe_path = os.path.join(exe_dir, self.env["app_name"])

        # 确保可执行文件存在
        if not os.path.exists(exe_path):
            # 尝试检查带.exe扩展名的文件
            alt_exe_path = f"{exe_path}.exe"
            if os.path.exists(alt_exe_path):
                # 尝试修复文件名
                try:
                    os.rename(alt_exe_path, exe_path)
                    print(f"已将文件重命名为: {exe_path}")
                except Exception as e:
                    print(f"尝试重命名文件失败: {e}")
                    return False
            else:
                print(f"错误: 找不到Linux可执行文件，无法创建安装包: {exe_path}")
                return False

        # 确保可执行文件有执行权限
        try:
            os.chmod(exe_path, 0o755)
        except Exception as e:
            print(f"添加执行权限失败: {e}")

        # 创建输出目录
        installer_dir = self.env["installer_dir"]
        os.makedirs(installer_dir, exist_ok=True)

        # 创建桌面文件
        if self.platform_config.get("desktop_entry", False):
            desktop_file = os.path.join(
                self.env["temp_dir"], f"{self.env['app_name']}.desktop")

            # 创建桌面快捷方式文件
            with open(desktop_file, 'w', encoding='utf-8-sig') as f:
                f.write(f"""[Desktop Entry]
Name={self.env['display_name']}
Comment={self.platform_config.get('description', 'Python Application')}
Exec={self.env['app_name']}
Icon={self.env['app_name']}
Terminal=false
Type=Application
Categories={self.platform_config.get('categories', 'Utility')}
""")

            # 复制到目标目录
            shutil.copy(desktop_file, os.path.join(
                exe_dir, f"{self.env['app_name']}.desktop"))
            print(
                f"已创建Linux桌面快捷方式: {os.path.join(exe_dir, self.env['app_name'])}.desktop")

        # 根据格式选择打包方式
        if install_format == "appimage":
            # 构建AppImage包
            return self._build_appimage(exe_dir)
        elif install_format == "deb":
            # 构建DEB包
            return self._build_deb(exe_dir)
        elif install_format == "rpm":
            # 构建RPM包
            return self._build_rpm(exe_dir)
        else:
            print(f"错误: 不支持的安装包格式: {install_format}")
            print("支持的格式: appimage, deb, rpm")
            return False

    def _build_appimage(self, exe_dir):
        """构建AppImage包"""
        # 检查appimagetool是否已安装
        if not self._check_tool("appimagetool"):
            print("错误: 未安装appimagetool，无法创建AppImage")
            print("请参考: https://github.com/AppImage/AppImageKit/releases")
            return False

        print("开始构建AppImage...")

        # 准备AppDir目录
        temp_dir = tempfile.mkdtemp(prefix=f"{self.env['app_name']}_appimage_")
        app_dir = os.path.join(temp_dir, "AppDir")
        os.makedirs(app_dir, exist_ok=True)

        # 复制应用程序文件到AppDir
        try:
            for item in os.listdir(exe_dir):
                src = os.path.join(exe_dir, item)
                dst = os.path.join(app_dir, item)

                if os.path.isdir(src):
                    shutil.copytree(src, dst, symlinks=True)
                else:
                    shutil.copy2(src, dst)

            # 创建AppRun文件
            apprun_path = os.path.join(app_dir, "AppRun")
            with open(apprun_path, 'w', encoding='utf-8-sig') as f:
                f.write(f"""#!/bin/sh
# 获取AppImage或AppDir的路径
SELF_DIR=$(dirname "$(readlink -f "$0")")
# 运行应用
exec "$SELF_DIR/{self.env['app_name']}" "$@"
""")
            # 设置AppRun可执行权限
            os.chmod(apprun_path, 0o755)
            print(f"已创建AppRun启动脚本: {apprun_path}")

            # 处理图标
            if self.env.get("icon_path") and os.path.exists(self.env["icon_path"]):
                # 尝试转换图标到PNG格式（如果是ico格式）
                icon_path = self.env["icon_path"]
                icon_ext = os.path.splitext(icon_path)[1].lower()
                icon_name = f"{self.env['app_name']}{icon_ext}"

                # 复制图标到AppDir根目录
                target_icon = os.path.join(app_dir, icon_name)
                shutil.copy(icon_path, target_icon)
                print(f"已复制图标到AppDir: {target_icon}")
        except Exception as e:
            print(f"准备AppDir目录失败: {e}")
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"清理临时目录失败: {e}")
            return False

        # 定义AppImage输出路径
        installer_dir = self.env["installer_dir"]
        os.makedirs(installer_dir, exist_ok=True)
        appimage_path = os.path.join(
            installer_dir,
            f"{self.env['app_name']}-{self.env['version']}-x86_64.AppImage")

        # 构建appimagetool命令
        appimagetool_cmd = ["appimagetool", app_dir, appimage_path]

        # 执行appimagetool命令
        try:
            print(f"\n{'='*60}")
            print("步骤: 创建AppImage")
            print(f"{'='*60}")
            print(f"执行命令: {' '.join(appimagetool_cmd)}")

            result = subprocess.run(appimagetool_cmd, check=False)

            if result.returncode == 0:
                print("\n✓ 创建AppImage完成！")
                success = True
            else:
                print("\n❌ 创建AppImage失败！")
                success = False
        except Exception as e:
            print(f"\n❌ 创建AppImage失败: {e}")
            success = False

        # 清理临时目录
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"警告: 清理临时目录失败: {e}")

        # 验证输出
        if success and os.path.exists(appimage_path):
            size_mb = os.path.getsize(appimage_path) / (1024 * 1024)
            print(f"\nAppImage已创建: {appimage_path}")
            print(f"文件大小: {size_mb:.2f} MB")
            return True
        else:
            print(f"错误: 未能找到生成的AppImage: {appimage_path}")
            return False

    def _build_deb(self, exe_dir):
        """构建Debian包"""
        # 检查dpkg-deb是否已安装
        if not self._check_tool("dpkg-deb"):
            print("错误: 未安装dpkg-deb，无法创建Debian包")
            print("请安装: apt-get install dpkg-dev")
            return False

        print("开始构建Debian包...")

        # 准备DEB包结构
        temp_dir = tempfile.mkdtemp(prefix=f"{self.env['app_name']}_deb_")
        package_dir = os.path.join(
            temp_dir, f"{self.env['app_name']}_{self.env['version']}")

        # 创建所需的目录结构
        usr_dir = os.path.join(package_dir, "usr")
        bin_dir = os.path.join(usr_dir, "bin")
        share_dir = os.path.join(usr_dir, "share")
        app_dir = os.path.join(share_dir, self.env["app_name"])
        desktop_dir = os.path.join(share_dir, "applications")
        icon_dir = os.path.join(share_dir, "icons/hicolor/256x256/apps")
        debian_dir = os.path.join(package_dir, "DEBIAN")

        # 创建目录
        for d in [bin_dir, app_dir, desktop_dir, icon_dir, debian_dir]:
            os.makedirs(d, exist_ok=True)

        # 复制应用程序文件到app_dir
        for item in os.listdir(exe_dir):
            src = os.path.join(exe_dir, item)
            dst = os.path.join(app_dir, item)

            if os.path.isdir(src):
                shutil.copytree(src, dst, symlinks=True)
            else:
                shutil.copy2(src, dst)

        # 创建启动脚本
        launcher_script = os.path.join(bin_dir, self.env["app_name"])
        with open(launcher_script, 'w', encoding='utf-8') as f:
            f.write(f"""#!/bin/sh
exec /usr/share/{self.env["app_name"]}/{self.env["app_name"]} "$@"
""")

        # 设置可执行权限
        os.chmod(launcher_script, 0o755)

        # 创建桌面文件
        desktop_file = os.path.join(
            desktop_dir, f"{self.env['app_name']}.desktop")
        with open(desktop_file, 'w', encoding='utf-8') as f:
            f.write(f"""[Desktop Entry]
Type=Application
Name={self.env['display_name']}
Comment={self.platform_config.get('description', 'Python Application')}
Exec={self.env["app_name"]}
Icon={self.env["app_name"]}
Terminal=false
Categories={self.platform_config.get('categories', 'Utility')}
Version={self.env['version']}
""")

        # 处理图标
        if self.env.get("icon_path") and os.path.exists(self.env["icon_path"]):
            # 尝试转换图标到PNG格式（如果是ico格式）
            icon_path = self.env["icon_path"]
            icon_ext = os.path.splitext(icon_path)[1].lower()

            if icon_ext == ".ico":
                try:
                    import PIL.Image
                    img = PIL.Image.open(icon_path)
                    png_path = os.path.join(
                        temp_dir, f"{self.env['app_name']}.png")
                    img.save(png_path)
                    icon_path = png_path
                    icon_ext = ".png"
                    print(f"已将ICO图标转换为PNG格式: {png_path}")
                except ImportError:
                    print("警告: 未安装PIL，无法转换ICO图标")

            # 复制图标到图标目录
            target_icon = os.path.join(
                icon_dir, f"{self.env['app_name']}{icon_ext}")
            shutil.copy(icon_path, target_icon)
            print(f"已复制图标到: {target_icon}")

        # 创建control文件
        control_file = os.path.join(debian_dir, "control")

        # 处理依赖
        depends = "libc6"
        if self.platform_config.get("requires"):
            depends += ", " + self.platform_config.get("requires")

        with open(control_file, 'w', encoding='utf-8') as f:
            f.write(f"""Package: {self.env["app_name"]}
Version: {self.env['version']}
Section: utils
Priority: optional
Architecture: amd64
Depends: {depends}
Maintainer: {self.env.get('publisher', 'Python Packager')} <support@example.com>
Description: {self.platform_config.get('description', 'Python Application')}
 Python application packaged with PyInstaller
""")

        # 定义deb包输出路径
        deb_path = os.path.join(
            self.env["installer_dir"],
            f"{self.env['app_name']}_{self.env['version']}_amd64.deb")

        # 构建dpkg-deb命令
        deb_cmd = f"dpkg-deb --build {package_dir} {deb_path}"

        # 执行dpkg-deb命令
        success = self.run_command(deb_cmd, "创建Debian包")

        # 清理临时目录
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"警告: 清理临时目录失败: {e}")

        # 验证输出
        if success and os.path.exists(deb_path):
            size_mb = os.path.getsize(deb_path) / (1024 * 1024)
            print(f"\nDebian包已创建: {deb_path}")
            print(f"文件大小: {size_mb:.2f} MB")
            return True
        else:
            print(f"错误: 未能找到生成的Debian包: {deb_path}")
            return False

    def _build_rpm(self, exe_dir):
        """创建RPM包"""
        # 检查rpmbuild是否已安装
        if not self._check_tool("rpmbuild"):
            print("错误: 未安装rpmbuild，无法创建RPM包")
            print("请安装: yum install rpm-build 或 dnf install rpm-build")
            return False

        print("开始构建RPM包...")

        # 准备RPM构建环境
        home_dir = os.path.expanduser("~")
        rpm_dir = os.path.join(home_dir, "rpmbuild")
        spec_dir = os.path.join(rpm_dir, "SPECS")
        source_dir = os.path.join(rpm_dir, "SOURCES")

        # 创建目录
        for d in [spec_dir, source_dir]:
            os.makedirs(d, exist_ok=True)

        # 创建tar包
        tar_name = f"{self.env['app_name']}-{self.env['version']}"
        tar_path = os.path.join(source_dir, f"{tar_name}.tar.gz")

        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix=f"{self.env['app_name']}_rpm_")
        app_temp_dir = os.path.join(temp_dir, tar_name)
        os.makedirs(app_temp_dir, exist_ok=True)

        # 复制应用程序文件到临时目录
        for item in os.listdir(exe_dir):
            src = os.path.join(exe_dir, item)
            dst = os.path.join(app_temp_dir, item)

            if os.path.isdir(src):
                shutil.copytree(src, dst, symlinks=True)
            else:
                shutil.copy2(src, dst)

        # 创建桌面文件
        desktop_file = os.path.join(
            app_temp_dir, f"{self.env['app_name']}.desktop")
        with open(desktop_file, 'w', encoding='utf-8-sig') as f:
            f.write(f"""[Desktop Entry]
Type=Application
Name={self.env['display_name']}
Comment={self.platform_config.get('description', 'Python Application')}
Exec={self.env["app_name"]}
Icon={self.env["app_name"]}
Terminal=false
Categories={self.platform_config.get('categories', 'Utility')}
Version={self.env['version']}
""")

        # 创建tar包
        tar_cmd = f"tar -czf {tar_path} -C {temp_dir} {tar_name}"
        if not self.run_command(tar_cmd, "创建源码包"):
            return False

        # 创建spec文件
        spec_file = os.path.join(spec_dir, f"{self.env['app_name']}.spec")

        # 处理依赖
        requires = ""
        if self.platform_config.get("requires"):
            requires = "Requires: " + self.platform_config.get("requires")

        with open(spec_file, 'w', encoding='utf-8-sig') as f:
            f.write(f"""Name:           {self.env['app_name']}
Version:        {self.env['version']}
Release:        1%{{?dist}}
Summary:        {self.platform_config.get('description', 'Python Application')}

License:        Proprietary
URL:            http://example.com
Source0:        %{{name}}-%{{version}}.tar.gz

BuildArch:      x86_64
{requires}

%description
Python application packaged with PyInstaller

%prep
%setup -q

%install
mkdir -p %{{buildroot}}/usr/bin
mkdir -p %{{buildroot}}/usr/share/%{{name}}
mkdir -p %{{buildroot}}/usr/share/applications
mkdir -p %{{buildroot}}/usr/share/icons/hicolor/256x256/apps

# 复制应用程序文件
cp -r * %{{buildroot}}/usr/share/%{{name}}/

# 创建启动脚本
cat > %{{buildroot}}/usr/bin/%{{name}} << EOF
#!/bin/sh
exec /usr/share/%{{name}}/%{{name}} "$@"
EOF
chmod 755 %{{buildroot}}/usr/bin/%{{name}}

# 复制桌面文件
cp %{{name}}.desktop %{{buildroot}}/usr/share/applications/

%files
%{{_bindir}}/%{{name}}
%{{_datadir}}/%{{name}}/
%{{_datadir}}/applications/%{{name}}.desktop

%changelog
* {datetime.now().strftime("%a %b %d %Y")} {self.env.get('publisher', 'Developer')} <dev@example.com> - {self.env['version']}-1
- Initial package
""")

        # 设置输出目录
        installer_dir = self.env["installer_dir"]
        os.makedirs(installer_dir, exist_ok=True)

        # 构建rpmbuild命令
        rpm_cmd = f"rpmbuild -ba {spec_file}"

        # 执行rpmbuild命令
        if not self.run_command(rpm_cmd, "构建RPM包"):
            return False

        # 查找生成的RPM包
        rpm_pattern = os.path.join(
            rpm_dir,
            "RPMS",
            "x86_64",
            f"{self.env['app_name']}-{self.env['version']}*.rpm")
        rpm_files = glob.glob(rpm_pattern)

        if not rpm_files:
            print(f"错误: 未能找到生成的RPM包: {rpm_pattern}")
            return False

        # 复制RPM包到输出目录
        rpm_file = rpm_files[0]
        output_rpm = os.path.join(installer_dir, os.path.basename(rpm_file))
        shutil.copy(rpm_file, output_rpm)

        # 清理临时目录
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"警告: 清理临时目录失败: {e}")

        # 验证输出
        if os.path.exists(output_rpm):
            size_mb = os.path.getsize(output_rpm) / (1024 * 1024)
            print(f"\nRPM包已创建: {output_rpm}")
            print(f"文件大小: {size_mb:.2f} MB")
            return True
        else:
            print(f"错误: 未能找到复制后的RPM包: {output_rpm}")
            return False

    def _check_tool(self, tool_name):
        """检查工具是否已安装"""
        try:
            subprocess.run(["which", tool_name],
                           check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def verify_output(self) -> bool:
        """验证Linux输出文件"""
        print("验证Linux输出文件...")

        # 检查可执行文件是否存在 - Linux上没有扩展名
        if self.env.get("onefile", False):
            # 单文件模式，可执行文件直接位于dist目录
            dist_dir = os.path.join(self.env["project_dir"], "dist")
            exe_path = os.path.join(dist_dir, self.env["app_name"])
        else:
            # 目录模式，可执行文件位于dist/app_name目录下
            app_name = self.env["app_name"]
            dist_dir = os.path.join(
                self.env["project_dir"], "dist", app_name)
            exe_path = os.path.join(dist_dir, app_name)

        # 验证可执行文件
        if not os.path.exists(exe_path):
            print(f"❌ 找不到Linux可执行文件: {exe_path}")

            # 尝试检查带.exe扩展名的文件（有时PyInstaller会错误地添加）
            alt_exe_path = f"{exe_path}.exe"
            if os.path.exists(alt_exe_path):
                print(f"发现带.exe扩展名的可执行文件: {alt_exe_path}")

                # 尝试修复文件名
                try:
                    os.rename(alt_exe_path, exe_path)
                    print(f"已将文件重命名为: {exe_path}")

                    if os.path.exists(exe_path):
                        print(f"验证重命名后的文件存在: {exe_path}")
                    else:
                        print(f"警告: 重命名后文件不存在: {exe_path}")
                        return False
                except Exception as e:
                    print(f"尝试重命名文件失败: {e}")
                    return False
            else:
                return False

        # 确保Linux可执行文件有执行权限
        try:
            os.chmod(exe_path, 0o755)
            print("已为Linux可执行文件添加执行权限")
        except Exception as e:
            print(f"添加执行权限失败: {e}")

        # 显示文件信息
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024*1024)
            print(f"已确认Linux可执行文件存在: {exe_path}")
            print(f"文件大小: {size_mb:.2f} MB")

        # 检查桌面快捷方式
        if self.platform_config.get("desktop_entry", False):
            # 桌面文件路径
            desktop_file = None
            if self.env.get("onefile", False):
                desktop_file = os.path.join(
                    dist_dir, f"{self.env['app_name']}.desktop")
            else:
                desktop_file = os.path.join(
                    dist_dir, f"{self.env['app_name']}.desktop")

            if os.path.exists(desktop_file):
                print(f"已确认Linux桌面快捷方式存在: {desktop_file}")
            else:
                print(f"警告: 未找到Linux桌面快捷方式: {desktop_file}")

        # 验证安装包文件（如果不跳过安装程序）
        if not self.env.get("skip_installer", False):
            target_format = self.platform_config.get(
                "format", "appimage").lower()
            installer_dir = self.env["installer_dir"]

            # 检查对应格式的安装包
            if target_format == "appimage":
                package_path = os.path.join(
                    installer_dir,
                    f"{self.env['app_name']}-{self.env['version']}-x86_64.AppImage")
            elif target_format == "deb":
                package_path = os.path.join(
                    installer_dir,
                    f"{self.env['app_name']}_{self.env['version']}_amd64.deb")
            elif target_format == "rpm":
                # RPM包命名格式可能有多样性，使用glob查找
                pattern = os.path.join(
                    installer_dir,
                    f"{self.env['app_name']}-{self.env['version']}*.rpm")
                matches = glob.glob(pattern)
                if matches:
                    package_path = matches[0]
                else:
                    package_path = None
                    print(f"❌ 找不到RPM安装包: {pattern}")
            else:
                print(f"不支持验证 {target_format} 格式的安装包")
                package_path = None

            # 验证安装包文件
            if package_path and os.path.exists(package_path):
                size_mb = os.path.getsize(package_path) / (1024*1024)
                print(f"已确认{target_format.upper()}安装包存在: {package_path}")
                print(f"文件大小: {size_mb:.2f} MB")
            else:
                print(f"❌ 找不到{target_format.upper()}安装包: {package_path}")
                # 不因为安装包失败而返回错误，因为可执行文件已经构建成功

        return True


class PackagerFactory:
    """打包器工厂类，根据平台创建对应的打包器"""

    @staticmethod
    def create_packager(env: Dict[str, Any]) -> PlatformPackager:
        """
        创建适合当前平台的打包器

        Args:
            env: 打包环境信息和配置

        Returns:
            对应平台的打包器实例
        """
        system = platform.system().lower()

        # 从配置中获取特定平台的配置
        platform_config = {}
        if "platform_specific" in env:
            if system == "windows" and "windows" in env["platform_specific"]:
                platform_config = env["platform_specific"]["windows"]
            elif system == "darwin" and "macos" in env["platform_specific"]:
                platform_config = env["platform_specific"]["macos"]
            elif system == "linux" and "linux" in env["platform_specific"]:
                platform_config = env["platform_specific"]["linux"]

        # 将平台特定配置添加到环境中
        env["platform_config"] = platform_config

        # 根据系统选择打包器
        if system == "windows":
            return WindowsPackager(env)
        elif system == "darwin":
            return MacOSPackager(env)
        elif system == "linux":
            return LinuxPackager(env)
        else:
            raise ValueError(f"不支持的操作系统: {system}")
