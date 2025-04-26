#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows安装程序构建工具
使用Inno Setup将可执行文件打包为Windows安装程序
"""

import os
import sys
import subprocess
import tempfile
import shutil
import urllib.request
import argparse
import time
import glob


# Inno Setup 下载URL
INNO_SETUP_URL = "https://files.jrsoftware.org/is/6/innosetup-6.2.1.exe"
INNO_SETUP_INSTALLER = "innosetup-6.2.1.exe"


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="构建Windows安装程序")

    parser.add_argument("--name", required=True, help="应用程序名称")
    parser.add_argument("--iss", required=True, help="Inno Setup脚本文件路径")
    parser.add_argument("--exe", help="可执行文件路径")
    parser.add_argument("--output", help="输出目录路径")
    parser.add_argument(
        "--inno-path", help="Inno Setup可执行文件路径(ISCC.exe)", default=None)

    args = parser.parse_args()

    # 处理inno-path参数，移除可能存在的引号
    if args.inno_path:
        args.inno_path = args.inno_path.strip('"\'')

    return args


def download_file(url, destination):
    """下载文件到指定位置"""
    print(f"正在下载 {url} 到 {destination}...")

    try:
        with urllib.request.urlopen(url) as response:
            with open(destination, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        print("下载完成!")
        return True
    except Exception as e:
        print(f"下载失败: {e}")
        return False


def check_inno_setup(custom_path=None):
    """检查Inno Setup是否已安装"""
    # 如果提供了自定义路径，首先检查它
    if custom_path and os.path.exists(custom_path):
        return custom_path

    # 检查环境变量
    env_path = os.environ.get("INNO_SETUP_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    # 尝试通过注册表找到Inno Setup
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1") as key:
            install_dir = winreg.QueryValueEx(key, "InstallLocation")[0]
            iscc_path = os.path.join(install_dir, "ISCC.exe")
            if os.path.exists(iscc_path):
                return iscc_path
    except Exception:
        pass

    # 检查默认安装路径
    inno_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe"
    ]

    for path in inno_paths:
        if os.path.exists(path):
            return path

    return None


def install_inno_setup():
    """安装Inno Setup"""
    temp_dir = tempfile.gettempdir()
    installer_path = os.path.join(temp_dir, INNO_SETUP_INSTALLER)

    # 下载安装程序
    if not download_file(INNO_SETUP_URL, installer_path):
        return None

    # 运行安装程序
    print("正在安装Inno Setup...")
    print("请在弹出的安装向导中完成安装，接受默认设置即可。")

    try:
        subprocess.call([installer_path, "/VERYSILENT", "/SUPPRESSMSGBOXES"])

        # 检查是否安装成功
        return check_inno_setup()
    except Exception as e:
        print(f"安装失败: {e}")
        return None


def ensure_inno_setup(custom_path=None):
    """确保Inno Setup已安装"""
    inno_path = check_inno_setup(custom_path)

    if inno_path:
        print(f"检测到Inno Setup: {inno_path}")
        return inno_path

    print("未检测到Inno Setup！")
    print("\n" + "="*70)
    print("  请按照以下步骤手动安装Inno Setup:")
    print("  1. 访问 https://jrsoftware.org/isdl.php 下载最新版Inno Setup")
    print("  2. 运行下载的安装程序，按照向导完成安装")
    print("  3. 安装完成后，使用以下方式之一指定Inno Setup路径:")
    print("     - 通过--inno-path参数指定ISCC.exe的完整路径")
    print("     - 设置INNO_SETUP_PATH环境变量为ISCC.exe的完整路径")
    print("     - 使用默认安装路径(Program Files或Program Files (x86)下的Inno Setup 6目录)")
    print("="*70 + "\n")
    return None


def ensure_output_dirs():
    """确保输出目录存在"""
    # 创建installer目录
    if not os.path.exists("installer"):
        os.makedirs("installer")
        print("已创建installer目录")

    # 确保dist目录存在
    if not os.path.exists("dist"):
        print("警告: dist目录不存在，请先运行PyInstaller打包!")
        print("是否继续? (y/n): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            return False

    return True


def sanitize_filename(filename):
    """处理文件名，确保其安全有效"""
    # 移除可能在路径中引起问题的字符
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def find_newly_created_file(directory, pattern, before_time):
    """查找新创建的文件"""
    files = []
    for file in glob.glob(os.path.join(directory, pattern)):
        creation_time = os.path.getctime(file)
        if creation_time > before_time:
            files.append((file, creation_time))

    # 按创建时间排序，最新的在前
    files.sort(key=lambda x: x[1], reverse=True)
    return [f[0] for f in files]


def build_installer(inno_path, args):
    """使用Inno Setup构建安装程序"""
    print("\n开始构建安装程序...")

    # 检查Inno Setup路径是否存在
    if not os.path.exists(inno_path):
        print(f"错误: 找不到Inno Setup路径: {inno_path}")
        return False

    # 记录开始时间，用于查找新创建的文件
    start_time = time.time()

    # 获取输出目录
    output_dir = args.output if args.output else "installer"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已创建输出目录: {output_dir}")

    # 获取一个安全的应用名称用于文件名
    safe_name = sanitize_filename(args.name)

    # 确认dist目录中有可执行文件
    exe_name = f"{args.name}.exe"

    # 如果提供了exe路径，则使用它，否则尝试在多个位置查找
    if args.exe and os.path.exists(args.exe):
        exe_path = args.exe
    else:
        # 首先在直接目录模式下查找
        exe_path = os.path.join("dist", args.name, exe_name)

        # 如果不存在，则尝试单文件模式路径
        if not os.path.exists(exe_path):
            exe_path = os.path.join("dist", exe_name)

        # 如果两种路径都不存在，则报错
        if not os.path.exists(exe_path):
            print("错误: 找不到可执行文件，已尝试以下路径:")
            print(f"  - {os.path.join('dist', args.name, exe_name)}")
            print(f"  - {os.path.join('dist', exe_name)}")
            return False

    print(f"已确认可执行文件存在: {exe_path}")

    # 执行Inno Setup编译
    try:
        # 首先检查setup.iss是否存在
        if not os.path.exists(args.iss):
            print(f"错误: 找不到setup.iss文件: {args.iss}")
            return False

        # 创建临时ISS文件，替换路径为绝对路径
        with open(args.iss, 'r', encoding='utf-8') as f:
            iss_content = f.read()

        # 获取绝对路径
        abs_exe_path = os.path.abspath(exe_path)
        dist_dir = os.path.dirname(abs_exe_path)

        # 替换相对路径为绝对路径
        iss_content = iss_content.replace(
            'Source: "dist\\', f'Source: "{dist_dir}\\')

        # 写入临时文件
        temp_iss = args.iss + ".temp"
        with open(temp_iss, 'w', encoding='utf-8') as f:
            f.write(iss_content)

        # 运行Inno Setup命令
        print(f"运行Inno Setup: {inno_path} {temp_iss}")
        try:
            # 使用列表形式的命令以正确处理带空格的路径
            iscc_cmd = [inno_path, temp_iss]
            result = subprocess.run(
                iscc_cmd,
                capture_output=True,
                text=True,
                shell=False  # 设置为False以避免shell解析的问题
            )

            # 删除临时文件
            try:
                os.remove(temp_iss)
            except Exception:
                # 忽略删除临时文件时的错误
                pass

            # 检查执行结果
            if result.returncode != 0:
                print(f"Inno Setup编译失败，返回码: {result.returncode}")
                print("错误输出:")
                print(result.stderr)
                print("标准输出:")
                print(result.stdout)
                return False
            else:
                print("Inno Setup编译成功!")

            # 等待文件生成
            time.sleep(2)

            # 查找新创建的文件
            new_files = find_newly_created_file(
                output_dir, "*.exe", start_time)

            # 列出installer目录中的所有文件
            print(f"{output_dir}目录内容:")
            setup_file = None

            for f in os.listdir(output_dir):
                full_path = os.path.join(output_dir, f)
                if os.path.isfile(full_path) and f.endswith(".exe"):
                    size = os.path.getsize(full_path) / (1024 * 1024)
                    print(f"  - {f} ({size:.2f} MB)")

                    # 如果是新创建的文件，标记为可能的安装程序
                    if full_path in new_files:
                        print("    (新创建的文件)")
                        setup_file = full_path

            # 如果找到了新创建的文件
            if setup_file:
                print(f"安装程序生成成功: {os.path.abspath(setup_file)}")
                size_mb = os.path.getsize(setup_file) / (1024 * 1024)
                print(f"文件大小: {size_mb:.2f} MB")
                return True
            else:
                # 检查几个可能的命名模式
                possible_names = [
                    f"{safe_name}_Setup.exe",
                    f"{args.name}_Setup.exe",
                    "Setup.exe"
                ]

                for name in possible_names:
                    full_path = os.path.join(output_dir, name)
                    if os.path.exists(full_path):
                        print(f"找到可能的安装程序: {os.path.abspath(full_path)}")
                        return True

                print("未能找到生成的安装程序文件")
                return False
        except Exception as e:
            print(f"运行Inno Setup失败: {e}")
            return False

    except Exception as e:
        print(f"构建安装程序失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("Windows安装程序构建工具")
    print("=" * 60)

    # 解析命令行参数
    args = parse_arguments()

    # 确保输出目录存在
    if not ensure_output_dirs():
        print("已取消操作")
        return 1

    # 确保Inno Setup已安装，传入自定义路径
    inno_path = ensure_inno_setup(args.inno_path)
    if not inno_path:
        print("构建Windows安装程序需要Inno Setup，请安装后重试")
        return 1

    # 构建安装程序
    if build_installer(inno_path, args):
        print("\n恭喜! 安装包生成成功")
        return 0
    else:
        print("\n安装包生成失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
