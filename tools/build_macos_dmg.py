#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MacOS DMG镜像构建工具
用于将PyInstaller生成的.app文件打包为DMG镜像
"""

import os
import sys
import subprocess
import argparse
import shutil
import tempfile
from pathlib import Path


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="构建MacOS DMG安装镜像")

    parser.add_argument("--name", required=True, help="应用程序名称")
    parser.add_argument("--app", required=True, help="应用程序包路径(.app)")
    parser.add_argument("--output", help="输出DMG文件路径")
    parser.add_argument("--volume-name", help="DMG卷标名称")
    parser.add_argument("--background", help="DMG背景图片路径")
    parser.add_argument("--version", help="应用程序版本", default="1.0")
    parser.add_argument("--icon-size", help="图标大小", default="128")
    parser.add_argument("--sign", help="是否签名DMG", action="store_true")
    parser.add_argument("--identity", help="签名身份")

    return parser.parse_args()


def check_create_dmg():
    """检查create-dmg是否已安装"""
    try:
        subprocess.run(["which", "create-dmg"],
                       check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_create_dmg():
    """安装create-dmg"""
    print("未检测到create-dmg，尝试安装...")

    try:
        # 检查是否可以使用brew安装
        subprocess.run(["which", "brew"], check=True, capture_output=True)
        print("使用Homebrew安装create-dmg...")
        subprocess.run(["brew", "install", "create-dmg"], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("无法使用Homebrew安装create-dmg")
        print("请手动安装create-dmg: https://github.com/create-dmg/create-dmg")
        return False


def run_command(command, description):
    """运行命令并显示进度"""
    print(f"\n{'='*60}")
    print(f"步骤: {description}")
    print(f"{'='*60}")
    print(f"执行命令: {command}")

    try:
        result = subprocess.run(command, shell=True)

        if result.returncode == 0:
            print(f"\n✓ {description}完成！")
            return True
        else:
            print(f"\n❌ {description}失败！")
            return False
    except Exception as e:
        print(f"\n❌ {description}失败: {e}")
        return False


def sanitize_path(path):
    """处理路径，确保其安全有效"""
    return str(Path(path).absolute())


def create_dmg(args):
    """创建DMG安装镜像"""
    # 确保app路径存在
    app_path = sanitize_path(args.app)
    if not os.path.exists(app_path):
        print(f"错误: 找不到应用程序包: {app_path}")
        return False

    # 设置DMG输出路径
    if args.output:
        output_path = sanitize_path(args.output)
    else:
        # 默认输出到installer目录
        if os.path.isdir(app_path):
            parent_dir = os.path.dirname(os.path.dirname(app_path))
        else:
            parent_dir = os.path.dirname(app_path)

        output_dir = os.path.join(parent_dir, "installer")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(
            output_dir, f"{args.name}-{args.version}.dmg")

    # 设置DMG卷标
    volume_name = args.volume_name if args.volume_name else f"{args.name} {args.version}"

    # 构建create-dmg命令
    cmd = [
        "create-dmg",
        f"--volname \"{volume_name}\"",
        f"--icon-size {args.icon_size}",
        "--window-pos 200 120",
        "--window-size 800 400",
        "--app-drop-link 600 185",
    ]

    # 添加背景图片(如果提供)
    if args.background and os.path.exists(args.background):
        cmd.append(f"--background \"{sanitize_path(args.background)}\"")

    # 添加输出路径和app路径
    cmd.append(f"\"{output_path}\"")
    cmd.append(f"\"{app_path}\"")

    # 执行create-dmg命令
    success = run_command(" ".join(cmd), "创建DMG镜像")

    if not success:
        return False

    # 如果需要签名DMG
    if args.sign and args.identity:
        sign_cmd = f"codesign -s \"{args.identity}\" \"{output_path}\""
        sign_success = run_command(sign_cmd, "签名DMG镜像")

        if not sign_success:
            print("警告: DMG签名失败，但DMG镜像已成功创建")

    # 显示DMG路径和大小
    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"\nDMG镜像已创建: {output_path}")
        print(f"文件大小: {size_mb:.2f} MB")
        return True
    else:
        print(f"错误: 未能找到生成的DMG镜像: {output_path}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("MacOS DMG镜像构建工具")
    print("=" * 60)

    # 解析命令行参数
    args = parse_arguments()

    # 检查create-dmg是否已安装
    if not check_create_dmg():
        if not install_create_dmg():
            print("错误: 无法安装create-dmg，无法继续")
            return 1

    # 创建DMG
    if create_dmg(args):
        print("\n恭喜! DMG镜像创建成功")
        return 0
    else:
        print("\nDMG镜像创建失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
