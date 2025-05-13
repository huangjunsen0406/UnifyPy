#!/usr/bin/env python
# -*- coding: utf-8-sig -*-
"""
Linux安装包构建工具
用于将PyInstaller生成的文件打包为AppImage或deb/rpm包
"""

import os
import sys
import subprocess
import argparse
import shutil
import tempfile
import glob
from pathlib import Path


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="构建Linux安装包")

    parser.add_argument("--name", required=True, help="应用程序名称")
    parser.add_argument("--input", required=True, help="可执行文件目录路径")
    parser.add_argument("--output", help="输出安装包目录")
    parser.add_argument("--version", help="应用程序版本", default="1.0")
    parser.add_argument(
        "--description",
        help="应用程序描述",
        default="Python Application")
    parser.add_argument("--categories", help="应用程序分类", default="Utility")
    parser.add_argument("--icon", help="应用图标路径")
    parser.add_argument(
        "--format",
        help="安装包格式 (appimage, deb, rpm)",
        default="appimage")
    parser.add_argument("--requires", help="依赖包列表，逗号分隔")

    return parser.parse_args()


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


def check_tool(tool_name):
    """检查工具是否已安装"""
    try:
        subprocess.run(["which", tool_name], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def create_desktop_entry(args, target_dir):
    """创建桌面快捷方式文件"""
    desktop_file = os.path.join(target_dir, f"{args.name}.desktop")

    # 处理图标路径
    icon_path = args.name
    if args.icon and os.path.exists(args.icon):
        # 复制图标到目标目录
        icon_ext = os.path.splitext(args.icon)[1]
        new_icon_path = os.path.join(target_dir, f"{args.name}{icon_ext}")
        shutil.copy(args.icon, new_icon_path)
        icon_path = os.path.basename(new_icon_path)

    # 创建桌面快捷方式文件
    with open(desktop_file, 'w', encoding='utf-8-sig') as f:
        f.write(f"""[Desktop Entry]
Type=Application
Name={args.name}
Comment={args.description}
Exec={args.name}
Icon={icon_path}
Terminal=false
Categories={args.categories}
Version={args.version}
""")

    # 设置可执行权限
    os.chmod(desktop_file, 0o755)
    print(f"已创建桌面快捷方式: {desktop_file}")

    return desktop_file


def create_appimage(args):
    """创建AppImage包"""
    # 检查appimagetool是否已安装
    if not check_tool("appimagetool"):
        print("错误: 未安装appimagetool，无法创建AppImage")
        print("请参考: https://github.com/AppImage/AppImageKit/releases")
        return False

    # 准备AppDir目录
    temp_dir = tempfile.mkdtemp(prefix=f"{args.name}_appimage_")
    app_dir = os.path.join(temp_dir, "AppDir")
    os.makedirs(app_dir, exist_ok=True)

    # 复制应用程序文件到AppDir
    shutil.copytree(args.input, app_dir, symlinks=True, dirs_exist_ok=True)

    # 创建桌面文件
    desktop_file = create_desktop_entry(args, app_dir)

    # 在复制文件后，创建桌面文件前添加以下代码
    apprun_path = os.path.join(app_dir, "AppRun")
    with open(apprun_path, 'w', encoding='utf-8-sig') as f:
        f.write(f"""#!/bin/sh
# 获取AppImage或AppDir的路径
SELF_DIR=$(dirname "$(readlink -f "$0")")
# 运行应用
exec "$SELF_DIR/{args.name}" "$@"
""")
    os.chmod(apprun_path, 0o755)
    print(f"已创建AppRun文件: {apprun_path}")

    # 设置输出目录
    if args.output:
        output_dir = args.output
    else:
        output_dir = os.path.join(os.path.dirname(args.input), "installer")

    os.makedirs(output_dir, exist_ok=True)

    # 定义AppImage输出路径
    appimage_path = os.path.join(output_dir,
                                 f"{args.name}-{args.version}-x86_64.AppImage")

    # 构建appimagetool命令 - 使用列表而不是字符串，以避免命令行参数问题
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

    # 显示AppImage路径和大小
    if success and os.path.exists(appimage_path):
        size_mb = os.path.getsize(appimage_path) / (1024 * 1024)
        print(f"\nAppImage已创建: {appimage_path}")
        print(f"文件大小: {size_mb:.2f} MB")
        return True
    else:
        print(f"错误: 未能找到生成的AppImage: {appimage_path}")
        return False


def create_deb_package(args):
    """创建Debian包"""
    # 检查dpkg-deb是否已安装
    if not check_tool("dpkg-deb"):
        print("错误: 未安装dpkg-deb，无法创建Debian包")
        print("请安装: apt-get install dpkg-dev")
        return False

    # 准备Debian包结构
    temp_dir = tempfile.mkdtemp(prefix=f"{args.name}_deb_")
    package_dir = os.path.join(temp_dir, f"{args.name}_{args.version}")

    # 创建所需的目录结构
    usr_dir = os.path.join(package_dir, "usr")
    bin_dir = os.path.join(usr_dir, "bin")
    share_dir = os.path.join(usr_dir, "share")
    app_dir = os.path.join(share_dir, args.name)
    desktop_dir = os.path.join(share_dir, "applications")
    icon_dir = os.path.join(share_dir, "icons/hicolor/256x256/apps")
    debian_dir = os.path.join(package_dir, "DEBIAN")

    # 创建目录
    for d in [bin_dir, app_dir, desktop_dir, icon_dir, debian_dir]:
        os.makedirs(d, exist_ok=True)

    # 复制应用程序文件到app_dir
    shutil.copytree(args.input, app_dir, symlinks=True, dirs_exist_ok=True)

    # 创建启动脚本
    launcher_script = os.path.join(bin_dir, args.name)
    with open(launcher_script, 'w', encoding='utf-8-sig') as f:
        f.write(f"""#!/bin/sh
exec /usr/share/{args.name}/{args.name} "$@"
""")

    # 设置可执行权限
    os.chmod(launcher_script, 0o755)

    # 创建桌面文件
    desktop_file = os.path.join(desktop_dir, f"{args.name}.desktop")
    with open(desktop_file, 'w', encoding='utf-8-sig') as f:
        f.write(f"""[Desktop Entry]
Type=Application
Name={args.name}
Comment={args.description}
Exec={args.name}
Icon={args.name}
Terminal=false
Categories={args.categories}
Version={args.version}
""")

    # 处理图标
    if args.icon and os.path.exists(args.icon):
        # 复制图标到图标目录
        icon_ext = os.path.splitext(args.icon)[1]
        shutil.copy(
            args.icon,
            os.path.join(
                icon_dir,
                f"{args.name}{icon_ext}"))

    # 创建control文件
    control_file = os.path.join(debian_dir, "control")

    # 处理依赖
    depends = "libc6"
    if args.requires:
        depends += ", " + args.requires

    with open(control_file, 'w', encoding='utf-8-sig') as f:
        f.write(f"""Package: {args.name}
Version: {args.version}
Section: utils
Priority: optional
Architecture: amd64
Depends: {depends}
Maintainer: Python Packager <support@example.com>
Description: {args.description}
 Python application packaged with PyInstaller
""")

    # 设置输出目录
    if args.output:
        output_dir = args.output
    else:
        output_dir = os.path.join(os.path.dirname(args.input), "installer")

    os.makedirs(output_dir, exist_ok=True)

    # 定义deb包输出路径
    deb_path = os.path.join(
        output_dir,
        f"{args.name}_{args.version}_amd64.deb")

    # 构建dpkg-deb命令
    cmd = f"dpkg-deb --build {package_dir} {deb_path}"

    # 执行dpkg-deb命令
    success = run_command(cmd, "创建Debian包")

    # 清理临时目录
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"警告: 清理临时目录失败: {e}")

    # 显示deb包路径和大小
    if success and os.path.exists(deb_path):
        size_mb = os.path.getsize(deb_path) / (1024 * 1024)
        print(f"\nDebian包已创建: {deb_path}")
        print(f"文件大小: {size_mb:.2f} MB")
        return True
    else:
        print(f"错误: 未能找到生成的Debian包: {deb_path}")
        return False


def create_rpm_package(args):
    """创建RPM包"""
    # 检查rpmbuild是否已安装
    if not check_tool("rpmbuild"):
        print("错误: 未安装rpmbuild，无法创建RPM包")
        print("请安装: yum install rpm-build")
        return False

    # 准备RPM构建环境
    home_dir = os.path.expanduser("~")
    rpm_dir = os.path.join(home_dir, "rpmbuild")
    spec_dir = os.path.join(rpm_dir, "SPECS")
    source_dir = os.path.join(rpm_dir, "SOURCES")

    # 创建目录
    for d in [spec_dir, source_dir]:
        os.makedirs(d, exist_ok=True)

    # 创建tar包
    tar_name = f"{args.name}-{args.version}"
    tar_path = os.path.join(source_dir, f"{tar_name}.tar.gz")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix=f"{args.name}_rpm_")
    app_temp_dir = os.path.join(temp_dir, tar_name)
    os.makedirs(app_temp_dir, exist_ok=True)

    # 复制应用程序文件到临时目录
    shutil.copytree(
        args.input,
        app_temp_dir,
        symlinks=True,
        dirs_exist_ok=True)

    # 创建桌面文件
    desktop_file = create_desktop_entry(args, app_temp_dir)

    # 创建tar包
    tar_cmd = f"tar -czf {tar_path} -C {temp_dir} {tar_name}"
    if not run_command(tar_cmd, "创建源码包"):
        return False

    # 创建spec文件
    spec_file = os.path.join(spec_dir, f"{args.name}.spec")

    # 处理依赖
    requires = ""
    if args.requires:
        requires = "Requires: " + args.requires

    with open(spec_file, 'w', encoding='utf-8-sig') as f:
        f.write(f"""Name:           {args.name}
Version:        {args.version}
Release:        1%{{?dist}}
Summary:        {args.description}

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
* {subprocess.check_output(['date', '+%a %b %d %Y']).decode().strip()} Developer <dev@example.com> - {args.version}-1
- Initial package
""")

    # 设置输出目录
    if args.output:
        output_dir = args.output
    else:
        output_dir = os.path.join(os.path.dirname(args.input), "installer")

    os.makedirs(output_dir, exist_ok=True)

    # 构建rpmbuild命令
    rpm_cmd = f"rpmbuild -ba {spec_file}"

    # 执行rpmbuild命令
    if not run_command(rpm_cmd, "构建RPM包"):
        return False

    # 查找生成的RPM包
    rpm_pattern = os.path.join(
        rpm_dir,
        "RPMS",
        "x86_64",
        f"{args.name}-{args.version}*.rpm")
    rpm_files = glob.glob(rpm_pattern)

    if not rpm_files:
        print(f"错误: 未能找到生成的RPM包: {rpm_pattern}")
        return False

    # 复制RPM包到输出目录
    rpm_file = rpm_files[0]
    output_rpm = os.path.join(output_dir, os.path.basename(rpm_file))
    shutil.copy(rpm_file, output_rpm)

    # 清理临时目录
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"警告: 清理临时目录失败: {e}")

    # 显示RPM包路径和大小
    if os.path.exists(output_rpm):
        size_mb = os.path.getsize(output_rpm) / (1024 * 1024)
        print(f"\nRPM包已创建: {output_rpm}")
        print(f"文件大小: {size_mb:.2f} MB")
        return True
    else:
        print(f"错误: 未能找到复制后的RPM包: {output_rpm}")
        return False


def install_appimagetool():
    """安装appimagetool"""
    print("正在安装appimagetool...")

    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="appimagetool_install_")
    os.chdir(temp_dir)

    # 下载最新的appimagetool
    download_cmd = [
        "wget", "-c",
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage",
        "-O", "appimagetool"
    ]
    if not run_command(download_cmd, "下载appimagetool", shell=False):
        return False

    # 设置执行权限
    chmod_cmd = ["chmod", "+x", "appimagetool"]
    if not run_command(chmod_cmd, "设置appimagetool执行权限", shell=False):
        return False

    # 移动到系统路径
    move_cmd = ["sudo", "mv", "appimagetool", "/usr/local/bin/"]
    print("需要管理员权限来安装appimagetool到系统目录")
    if not run_command(move_cmd, "安装appimagetool到系统目录", shell=False):
        return False

    # 清理临时目录
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"警告: 清理临时目录失败: {e}")

    print("appimagetool安装完成！")
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("Linux安装包构建工具")
    print("=" * 60)

    # 解析命令行参数
    args = parse_arguments()

    # 检查输入目录是否存在
    if not os.path.exists(args.input):
        print(f"错误: 输入目录不存在: {args.input}")
        return 1

    # 根据格式选择打包方式
    if args.format.lower() == "appimage":
        print("选择的打包格式: AppImage")
        if create_appimage(args):
            print("\n恭喜! AppImage创建成功")
            return 0
        else:
            print("\nAppImage创建失败")
            return 1
    elif args.format.lower() == "deb":
        print("选择的打包格式: Debian包")
        if create_deb_package(args):
            print("\n恭喜! Debian包创建成功")
            return 0
        else:
            print("\nDebian包创建失败")
            return 1
    elif args.format.lower() == "rpm":
        print("选择的打包格式: RPM包")
        if create_rpm_package(args):
            print("\n恭喜! RPM包创建成功")
            return 0
        else:
            print("\nRPM包创建失败")
            return 1
    else:
        print(f"错误: 不支持的打包格式: {args.format}")
        print("支持的格式: appimage, deb, rpm")
        return 1


if __name__ == "__main__":
    sys.exit(main())
