#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python 项目通用打包工具
用于将Python项目打包为独立可执行文件和Windows安装程序
"""

import os
import sys
import json
import argparse
import shutil
import subprocess
import time


# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(SCRIPT_DIR, "tools")
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, "templates")


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
    
    # 复制模板文件
    setup_iss_template = os.path.join(TEMPLATES_DIR, "setup.iss.template")
    setup_iss_path = os.path.join(temp_dir, "setup.iss")
    
    # 读取模板内容
    with open(setup_iss_template, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # 替换模板变量
    template_content = template_content.replace(
        "{{APP_NAME}}", app_name)
    template_content = template_content.replace(
        "{{APP_VERSION}}", args.version)
    template_content = template_content.replace(
        "{{APP_PUBLISHER}}", args.publisher)
    template_content = template_content.replace(
        "{{DISPLAY_NAME}}", display_name)
    
    # 添加dist目录和installer目录的绝对路径
    source_path = os.path.abspath(os.path.join(args.project_dir, "dist"))
    template_content = template_content.replace(
        "{{SOURCE_PATH}}", source_path)
    
    output_path = os.path.abspath(os.path.join(args.project_dir, "installer"))
    template_content = template_content.replace(
        "{{OUTPUT_PATH}}", output_path)
    
    # 写入处理后的模板
    with open(setup_iss_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    # 处理图标
    if args.icon and os.path.exists(args.icon):
        icon_path = os.path.join(temp_dir, "app.ico")
        shutil.copy(args.icon, icon_path)
        print(f"已复制图标: {args.icon}")
    else:
        # 生成默认图标
        run_command(
            f"python {os.path.join(temp_dir, 'create_icon.py')}", 
            "生成默认图标")
    
    # 处理许可证文件
    if args.license and os.path.exists(args.license):
        license_path = os.path.join(temp_dir, "LICENSE.txt")
        shutil.copy(args.license, license_path)
        print(f"已复制许可证: {args.license}")
    
    # 处理自述文件
    if args.readme and os.path.exists(args.readme):
        readme_path = os.path.join(temp_dir, "README.md")
        shutil.copy(args.readme, readme_path)
        print(f"已复制自述文件: {args.readme}")
    
    return {
        "app_name": app_name,
        "display_name": display_name,
        "temp_dir": temp_dir,
        "entry_file": args.entry,
        "project_dir": args.project_dir,
        "hooks_dir": args.hooks,
        "installer_dir": installer_dir
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
    print("\n" + "="*70)
    print("          Python项目通用打包工具          ")
    print("="*70 + "\n")
    
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
    
    # 准备构建环境
    env = prepare_build_environment(args, config)
    
    # 步骤1: 构建可执行文件
    if not args.skip_exe:
        if not build_executable(env):
            print("构建可执行文件失败，中止打包过程")
            cleanup(env)
            return 1
    else:
        print("跳过可执行文件构建步骤")
    
    # 等待一秒，确保文件都已写入
    time.sleep(1)
    
    # 检查可执行文件是否存在
    exe_path = os.path.join(
        args.project_dir, "dist", f"{env['app_name']}.exe")
    if not os.path.exists(exe_path):
        print(f"❌ 找不到可执行文件: {exe_path}")
        print("打包过程中断！")
        cleanup(env)
        return 1
    
    print(f"已确认可执行文件存在: {exe_path}")
    print(f"文件大小: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")
    
    # 步骤2: 构建安装程序
    if not args.skip_installer:
        if not build_installer(env):
            print("构建安装程序失败")
            cleanup(env)
            return 1
    else:
        print("跳过安装程序构建步骤")
    
    # 打包完成 - 尝试多种可能的安装程序名称
    installer_pattern = f"{env['app_name']}_Setup.exe"
    installer_path = os.path.join(env["installer_dir"], installer_pattern)
    
    # 列出installer目录中的所有文件
    print("\n检查installer目录内容:")
    found_installer = None
    
    for f in os.listdir(env["installer_dir"]):
        if f.endswith(".exe"):
            full_path = os.path.join(env["installer_dir"], f)
            size_mb = os.path.getsize(full_path) / (1024*1024)
            print(f"  - {f} ({size_mb:.2f} MB)")
            
            # 保存找到的第一个安装程序
            if not found_installer:
                found_installer = full_path
    
    # 如果找到了安装程序，显示成功信息
    if found_installer:
        print("\n" + "="*70)
        print("            🎉 恭喜！完整打包流程已成功完成 🎉            ")
        print("="*70)
        print(f"\n可执行文件: {os.path.abspath(exe_path)}")
        exe_size = os.path.getsize(exe_path) / (1024*1024)
        print(f"文件大小: {exe_size:.2f} MB")
        print(f"\n安装程序: {os.path.abspath(found_installer)}")
        installer_size = os.path.getsize(found_installer) / (1024*1024)
        print(f"文件大小: {installer_size:.2f} MB")
        
        # 显示安装程序信息
        print("\n安装程序功能:")
        print("- 标准Windows安装界面")
        print("- 可选创建桌面快捷方式")
        print("- 可选设置开机自动启动")
        print("- 完整的卸载功能")
    else:
        print("\n打包过程可能未完全成功，未找到安装程序文件。")
    
    # 清理临时文件
    cleanup(env)
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 