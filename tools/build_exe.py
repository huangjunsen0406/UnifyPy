#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
可执行文件构建工具
使用PyInstaller将Python项目打包为独立可执行文件
"""

import sys
import subprocess
import os
import argparse
import shlex
import platform


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="构建Python项目为可执行文件")

    parser.add_argument("--name", required=True, help="应用程序名称")
    parser.add_argument("--entry", required=True, help="入口Python文件")
    parser.add_argument("--hooks", help="钩子目录路径")
    parser.add_argument("--icon", help="图标文件路径")
    parser.add_argument("--workdir", help="工作目录")
    parser.add_argument("--additional", help="附加PyInstaller参数")
    parser.add_argument("--onefile", help="生成单文件模式的可执行文件", action="store_true")

    return parser.parse_args()


def check_pyinstaller():
    """检查是否已安装PyInstaller"""
    try:
        # 尝试导入PyInstaller来检查是否已安装
        __import__("PyInstaller")
        return True
    except ImportError:
        return False


def install_pyinstaller():
    """安装PyInstaller"""
    print("正在安装PyInstaller...")
    cmd = [sys.executable, "-m", "pip", "install", "pyinstaller"]
    subprocess.check_call(cmd)
    print("PyInstaller安装完成！")


def ensure_hook_dir(hooks_dir):
    """确保钩子目录存在"""
    if not os.path.exists(hooks_dir):
        print(f"警告: 钩子目录 {hooks_dir} 不存在，将创建...")
        os.makedirs(hooks_dir)

    return hooks_dir


def build_executable(args):
    """使用PyInstaller打包程序"""
    print("正在打包程序...")

    # 确保工作目录存在
    work_dir = args.workdir if args.workdir else "."

    # 获取当前系统类型，用于确定可执行文件扩展名
    system = platform.system().lower()
    exe_extension = ".exe" if system == "windows" else ""

    # 创建spec文件路径
    spec_file = f"{args.name}.spec"
    spec_path = os.path.join(work_dir, spec_file)

    # 构建命令
    if os.path.exists(spec_path):
        print(f"发现已存在的spec文件: {spec_path}，将使用此文件打包")
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            spec_path
        ]
    else:
        print("创建新的打包配置...")
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller"
        ]

        # 选择打包模式 (单文件或目录模式)
        if args.onefile:
            cmd.append("--onefile")
            print("使用单文件模式打包")
        else:
            cmd.append("--onedir")
            # 为目录模式添加 contents-directory 参数，确保资源文件与可执行文件在同一目录
            cmd.extend(["--contents-directory", "."])
            print("使用目录模式打包，资源文件将与可执行文件处于同一级目录")

        # 添加应用名称
        cmd.extend(["--name", args.name])

        # 添加图标参数
        if args.icon and os.path.exists(args.icon):
            cmd.extend(["--icon", args.icon])
        else:
            cmd.extend(["--icon", "NONE"])  # 不使用图标

        # 添加钩子目录参数
        if args.hooks:
            hooks_dir = ensure_hook_dir(args.hooks)
            # 添加hook目录到PyInstaller的hookspath
            cmd.extend(["--additional-hooks-dir", hooks_dir])

            # 根据平台选择正确的路径分隔符
            separator = ":" if system in ["linux", "darwin"] else ";"
            # 如果hooks目录需要作为数据文件添加
            if system == "linux":
                # Linux平台使用等号格式
                cmd.append(
                    f"--add-data={hooks_dir}{separator}{os.path.basename(hooks_dir)}")
            else:
                # Windows和macOS平台使用空格格式
                cmd.extend(
                    ["--add-data", f"{hooks_dir}{separator}{os.path.basename(hooks_dir)}"])

        # 处理额外的PyInstaller参数
        if args.additional:
            print(f"添加额外的PyInstaller参数: {args.additional}")
            
            # 确保移除可能导致问题的外层引号
            additional_args = args.additional
            if ((additional_args.startswith('"') and additional_args.endswith('"')) or
                (additional_args.startswith("'") and additional_args.endswith("'"))):
                additional_args = additional_args[1:-1]
            
            # 检测当前平台，做适当处理
            if system == "linux":
                # Linux平台需要特别处理
                try:
                    # 使用shlex拆分参数，以处理复杂的引号和转义
                    splitted_args = shlex.split(additional_args)
                    
                    # 将 --add-data SOURCE:DEST 转换为 --add-data=SOURCE:DEST
                    i = 0
                    while i < len(splitted_args):
                        arg = splitted_args[i]
                        if arg == "--add-data" or arg == "--add-binary":
                            if i + 1 < len(splitted_args):
                                cmd.append(f"{arg}={splitted_args[i+1]}")
                                i += 2  # 跳过下一个参数
                                continue
                        cmd.append(arg)
                        i += 1
                except Exception as e:
                    print(f"处理附加参数时出错: {e}")
                    print("将使用原始附加参数")
                    # 如果处理失败，回退到简单地拆分参数
                    cmd.extend(additional_args.split())
            else:
                # Windows和macOS平台使用原始的分割方式
                cmd.extend(shlex.split(additional_args))

        # 添加入口文件
        cmd.append(args.entry)

    # 执行命令
    try:
        # 打印完整命令以便调试
        print(f"执行完整命令: {' '.join(cmd)}")
        
        # 使用subprocess.run执行命令，不使用shell=True
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print("\n打包完成！")

            # 根据打包模式和平台检查可执行文件
            if args.onefile:
                # 单文件模式，可执行文件直接位于dist目录
                exe_path = os.path.join("dist", f"{args.name}{exe_extension}")
            else:
                # 目录模式，可执行文件位于dist/app_name目录下
                exe_path = os.path.join(
                    "dist", args.name, f"{args.name}{exe_extension}")

            if os.path.exists(exe_path):
                print(f"可执行文件生成成功: {os.path.abspath(exe_path)}")
                print(f"文件大小: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")
                return True
            else:
                # 尝试尝试不带扩展名的版本（适用于某些特殊情况）
                if exe_extension and os.path.exists(os.path.splitext(exe_path)[0]):
                    alt_exe_path = os.path.splitext(exe_path)[0]
                    print(f"可执行文件生成成功: {os.path.abspath(alt_exe_path)}")
                    print(
                        f"文件大小: {os.path.getsize(alt_exe_path) / (1024*1024):.2f} MB")
                    return True

                print(f"警告: 可执行文件 {exe_path} 不存在，打包可能失败")
                return False
        else:
            print(f"打包失败，错误码: {result.returncode}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"打包失败，错误码: {e.returncode}")
        return False
    except Exception as e:
        print(f"执行命令时出错: {e}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("Python项目可执行文件构建工具")
    print("=" * 50)

    # 解析命令行参数
    args = parse_arguments()

    # 检查并安装PyInstaller
    if not check_pyinstaller():
        print("未检测到PyInstaller，准备安装...")
        install_pyinstaller()
    else:
        print("已检测到PyInstaller，准备打包...")

    # 打包程序
    if build_executable(args):
        print("\n可执行文件构建成功!")
        return 0
    else:
        print("\n可执行文件构建失败!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
