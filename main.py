#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UnifyPy
用于将Python项目打包为独立可执行文件和多平台安装程序
支持Windows、MacOS和Linux
"""

import os
import sys
import json
import argparse
import shutil
import subprocess
import time
import platform


# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(SCRIPT_DIR, "tools")
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, "templates")

# 导入平台工厂
sys.path.insert(0, TOOLS_DIR)
try:
    from platform_factory import PackagerFactory
except ImportError:
    print("错误: 找不到platform_factory模块，请确保tools/platform_factory.py文件存在")
    sys.exit(1)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="将Python项目打包为可执行文件和安装程序")

    parser.add_argument("project_dir", help="Python项目根目录路径")
    parser.add_argument(
        "--name", help="应用程序名称 (默认使用项目目录名称)", default=None)
    parser.add_argument(
        "--display-name", help="应用程序显示名称", default=None)
    parser.add_argument(
        "--entry", help="入口Python文件 (默认为main.py)", default="main.py")
    parser.add_argument(
        "--version", help="应用程序版本 (默认为1.0)", default="1.0")
    parser.add_argument(
        "--publisher", help="发布者名称", default="Python应用开发团队")
    parser.add_argument("--icon", help="图标文件路径", default=None)
    parser.add_argument("--license", help="许可证文件路径", default=None)
    parser.add_argument("--readme", help="自述文件路径", default=None)
    parser.add_argument("--config", help="配置文件路径 (JSON格式)", default=None)
    parser.add_argument("--hooks", help="运行时钩子目录", default=None)
    parser.add_argument("--skip-exe", help="跳过exe打包步骤", action="store_true")
    parser.add_argument(
        "--skip-installer", help="跳过安装程序生成步骤", action="store_true")
    parser.add_argument(
        "--onefile", help="生成单文件模式的可执行文件 (默认为目录模式)", action="store_true")
    parser.add_argument("--inno-setup-path",
                        help="Inno Setup可执行文件路径(ISCC.exe)", default=None)

    return parser.parse_args()


def load_config(config_path):
    """加载JSON配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}


def run_command(command, description, shell=True):
    """运行命令并显示进度"""
    print(f"\n{'='*60}")
    print(f"步骤: {description}")
    print(f"{'='*60}")
    print(f"执行命令: {command}")

    # 执行命令
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


def prepare_build_environment(args, config):
    """准备构建环境"""
    print("\n正在准备构建环境...")

    # 获取应用名称
    app_name = args.name
    if not app_name:
        app_name = os.path.basename(os.path.normpath(args.project_dir))
        print(f"未指定应用名称，将使用项目目录名称: {app_name}")

    # 获取显示名称 (如果提供)
    display_name = args.display_name if args.display_name else app_name

    # 创建临时目录结构
    temp_dir = os.path.join(args.project_dir, ".packaging_temp")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    # 创建目标目录
    dist_dir = os.path.join(args.project_dir, "dist")
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)

    installer_dir = os.path.join(args.project_dir, "installer")
    if not os.path.exists(installer_dir):
        os.makedirs(installer_dir)

    # 复制工具脚本到临时目录
    shutil.copy(os.path.join(TOOLS_DIR, "build_exe.py"), temp_dir)
    shutil.copy(os.path.join(TOOLS_DIR, "build_installer.py"), temp_dir)
    shutil.copy(os.path.join(TOOLS_DIR, "create_icon.py"), temp_dir)

    # 复制平台工厂到临时目录
    shutil.copy(os.path.join(TOOLS_DIR, "platform_factory.py"), temp_dir)

    # 处理图标
    icon_path = None
    if args.icon and os.path.exists(args.icon):
        icon_path = os.path.join(temp_dir, "app.ico")
        shutil.copy(args.icon, icon_path)
        print(f"已复制图标: {args.icon}")
    else:
        # 生成默认图标
        run_command(
            f"python {os.path.join(temp_dir, 'create_icon.py')}",
            "生成默认图标")
        icon_path = os.path.join(args.project_dir, "app.ico")

    # 处理许可证文件
    license_path = None
    if args.license and os.path.exists(args.license):
        license_path = os.path.join(temp_dir, "LICENSE.txt")
        shutil.copy(args.license, license_path)
        print(f"已复制许可证: {args.license}")

    # 处理自述文件
    readme_path = None
    if args.readme and os.path.exists(args.readme):
        readme_path = os.path.join(temp_dir, "README.md")
        shutil.copy(args.readme, readme_path)
        print(f"已复制自述文件: {args.readme}")

    # 获取配置中的额外PyInstaller参数
    additional_args = config.get("additional_pyinstaller_args", "")

    # 获取平台特定配置
    platform_specific = config.get("platform_specific", {})

    # 检测当前平台
    current_platform = platform.system().lower()
    if current_platform == "darwin":
        platform_name = "macOS"
    elif current_platform == "windows":
        platform_name = "Windows"
    elif current_platform == "linux":
        platform_name = "Linux"
    else:
        platform_name = current_platform.capitalize()

    print(f"检测到运行平台: {platform_name}")

    return {
        "app_name": app_name,
        "display_name": display_name,
        "temp_dir": temp_dir,
        "entry_file": args.entry,
        "project_dir": args.project_dir,
        "hooks_dir": args.hooks,
        "installer_dir": installer_dir,
        "onefile": args.onefile,
        "additional_args": additional_args,
        "skip_installer": args.skip_installer,
        "version": args.version,
        "publisher": args.publisher,
        "templates_dir": TEMPLATES_DIR,
        "platform_specific": platform_specific,
        "icon_path": icon_path,
        "license_path": license_path,
        "readme_path": readme_path,
        "inno_setup_path": args.inno_setup_path if hasattr(
            args,
            "inno_setup_path") else None,
    }


def build_executable(env):
    """构建可执行文件"""
    # 进入项目目录
    os.chdir(env["project_dir"])

    # 构建命令
    build_cmd = [
        sys.executable,
        os.path.join(env["temp_dir"], "build_exe.py"),
        "--name", env["app_name"],
        "--entry", env["entry_file"]
    ]

    # 添加钩子目录参数
    if env["hooks_dir"]:
        build_cmd.extend(["--hooks", env["hooks_dir"]])

    # 添加单文件模式参数(如果启用)
    if env.get("onefile", False):
        build_cmd.append("--onefile")
        print("使用单文件模式打包")
    else:
        print("使用目录模式打包，资源文件将与可执行文件处于同一级目录")

    # 添加额外的PyInstaller参数
    if env.get("additional_args"):
        # 将额外参数用引号包装，作为一个整体传递
        additional_args = env["additional_args"].replace('"', '\\"')  # 转义引号
        build_cmd.extend(["--additional", f'"{additional_args}"'])
        print(f"添加额外PyInstaller参数: {env['additional_args']}")

    # 执行构建
    return run_command(' '.join(build_cmd), "构建可执行文件")


def build_installer(env):
    """构建安装程序"""
    # 进入项目目录
    os.chdir(env["project_dir"])

    # 构建命令
    installer_cmd = [
        sys.executable,
        os.path.join(env["temp_dir"], "build_installer.py"),
        "--name", env["app_name"],
        "--iss", os.path.join(env["temp_dir"], "setup.iss")
    ]

    # 添加Inno Setup路径参数（如果有）
    if env.get("inno_setup_path"):
        installer_cmd.extend(["--inno-path", env["inno_setup_path"]])

    # 执行构建
    success = run_command(' '.join(installer_cmd), "构建安装程序")

    # 如果成功，等待一秒让文件系统更新
    if success:
        time.sleep(1)

    return success


def cleanup(env):
    """清理临时文件"""
    try:
        shutil.rmtree(env["temp_dir"])
        print("已清理临时文件")
    except Exception as e:
        print(f"清理临时文件失败: {e}")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("          Python项目通用打包工具          ")
    print("=" * 70 + "\n")

    # 解析命令行参数
    args = parse_arguments()

    # 将相对项目路径转换为绝对路径
    args.project_dir = os.path.abspath(args.project_dir)

    # 加载配置文件
    config = {}
    if args.config and os.path.exists(args.config):
        config = load_config(args.config)
        # 从配置文件中读取参数
        if "name" in config and not args.name:
            args.name = config["name"]
        if "display_name" in config and not args.display_name:
            args.display_name = config["display_name"]
        if "entry" in config and args.entry == "main.py":
            args.entry = config["entry"]
        if "version" in config and args.version == "1.0":
            args.version = config["version"]
        if "publisher" in config and args.publisher == "Python应用开发团队":
            args.publisher = config["publisher"]
        if "icon" in config and not args.icon:
            args.icon = config["icon"]
        if "license" in config and not args.license:
            args.license = config["license"]
        if "readme" in config and not args.readme:
            args.readme = config["readme"]
        if "hooks" in config and not args.hooks:
            args.hooks = config["hooks"]
        if "onefile" in config and not args.onefile:
            args.onefile = config["onefile"]
        if "skip_installer" in config:
            args.skip_installer = config["skip_installer"]
        if "inno_setup_path" in config and not args.inno_setup_path:
            args.inno_setup_path = config["inno_setup_path"]
        # 读取额外的PyInstaller参数
        if "additional_pyinstaller_args" in config:
            additional_args = config["additional_pyinstaller_args"]
            print(f"从配置文件加载额外PyInstaller参数: {additional_args}")

    # 准备构建环境
    env = prepare_build_environment(args, config)

    # 使用工厂模式创建平台适配的打包器
    try:
        packager = PackagerFactory.create_packager(env)
    except ValueError as e:
        print(f"错误: {e}")
        cleanup(env)
        return 1

    # 步骤1: 准备平台特定环境
    if not packager.prepare_environment():
        print("准备平台环境失败，中止打包过程")
        cleanup(env)
        return 1

    # 步骤2: 构建可执行文件
    if not args.skip_exe:
        if not packager.build_executable():
            print("构建可执行文件失败，中止打包过程")
            cleanup(env)
            return 1
    else:
        print("跳过可执行文件构建步骤")

    # 等待一秒，确保文件都已写入
    time.sleep(1)

    # 步骤3: 验证输出文件
    if not packager.verify_output():
        print("验证输出文件失败，打包过程可能未完全成功")
        cleanup(env)
        return 1

    # 步骤4: 构建安装程序(如果平台支持)
    if not args.skip_installer:
        if not packager.build_installer():
            print("构建安装程序失败")
            cleanup(env)
            return 1
    else:
        print("跳过安装程序构建步骤")

    # 打包完成
    print("\n" + "=" * 70)
    print("            🎉 恭喜！完整打包流程已成功完成 🎉            ")
    print("=" * 70)

    # 清理临时文件
    cleanup(env)

    return 0


if __name__ == "__main__":
    sys.exit(main())
