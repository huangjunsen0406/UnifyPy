#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux打包示例代码

本文件包含用于在Linux环境下打包Python应用程序的示例代码。
主要包括以下功能：
1. 使用PyInstaller构建Linux可执行文件
2. 创建Debian (.deb) 包
3. 创建RPM包
4. 创建AppImage可执行文件
5. 完整的打包工作流示例

使用前请确保已安装必要的依赖：
- PyInstaller: pip install pyinstaller
- 创建deb包: sudo apt-get install dpkg-dev fakeroot
- 创建rpm包: sudo apt-get install rpm
- 创建AppImage: 下载并安装appimagetool
"""

import os
import sys
import shutil
import subprocess
import platform
import glob
from pathlib import Path


def check_linux_environment():
    """
    检查当前Linux环境信息

    Returns:
        dict: 包含Linux环境信息的字典
    """
    if platform.system() != "Linux":
        print("错误: 当前不是Linux环境，无法执行Linux打包")
        return None

    # 获取Linux发行版信息
    env_info = {}
    try:
        # 检查是否存在/etc/os-release文件
        if os.path.exists('/etc/os-release'):
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        # 移除引号
                        env_info[key] = value.strip('"\'')

        # 获取Linux内核版本
        env_info['KERNEL'] = platform.release()

        # 系统架构
        env_info['ARCH'] = platform.machine()

        print(
            f"Linux发行版: {env_info.get('NAME', 'Unknown')} {env_info.get('VERSION', '')}")
        print(f"内核版本: {env_info['KERNEL']}")
        print(f"系统架构: {env_info['ARCH']}")

        return env_info
    except Exception as e:
        print(f"获取Linux环境信息失败: {e}")
        return None


def build_exe_with_pyinstaller(app_name, entry_file, workdir=None, onefile=False,
                               windowed=True, icon=None, additional_args=None):
    """
    使用PyInstaller构建Linux可执行文件

    Args:
        app_name: 应用程序名称
        entry_file: 入口文件路径
        workdir: 工作目录，默认为当前目录
        onefile: 是否打包为单个文件
        windowed: 是否以窗口模式运行
        icon: 图标文件路径
        additional_args: 附加的PyInstaller参数

    Returns:
        bool: 是否构建成功
    """
    if workdir:
        os.chdir(workdir)

    # 构建PyInstaller命令
    cmd = ["pyinstaller", "--clean"]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    if windowed:
        cmd.append("--windowed")

    if icon and os.path.exists(icon):
        cmd.extend(["--icon", icon])

    cmd.extend(["--name", app_name])

    # 添加额外的PyInstaller参数
    if additional_args:
        cmd.extend(additional_args.split())

    cmd.append(entry_file)

    # 执行PyInstaller
    try:
        print(f"执行命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        print(f"PyInstaller构建成功: {app_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller构建失败: {e}")
        return False


def create_desktop_entry(app_name, exec_path, icon_path=None, comment=None, categories=None):
    """
    创建Linux桌面入口文件 (.desktop)

    Args:
        app_name: 应用程序名称
        exec_path: 可执行文件路径
        icon_path: 图标文件路径
        comment: 应用程序描述
        categories: 应用程序分类

    Returns:
        str: 桌面入口文件内容
    """
    if categories is None:
        categories = ["Utility"]

    desktop_entry = f"""[Desktop Entry]
Name={app_name}
Exec={exec_path}
Terminal=false
Type=Application
"""

    if icon_path:
        desktop_entry += f"Icon={icon_path}\n"

    if comment:
        desktop_entry += f"Comment={comment}\n"

    desktop_entry += f"Categories={';'.join(categories)};\n"

    return desktop_entry


def create_debian_package(app_name, app_version, app_description, maintainer,
                          source_dir, architecture=None, dependencies=None):
    """
    创建Debian软件包(.deb)

    Args:
        app_name: 应用程序名称
        app_version: 应用程序版本
        app_description: 应用程序描述
        maintainer: 维护者信息
        source_dir: 源文件目录
        architecture: 目标架构，默认为当前系统架构
        dependencies: 依赖包列表

    Returns:
        str: 生成的.deb文件路径
    """
    if not architecture:
        # 获取当前系统架构
        if platform.machine() == 'x86_64':
            architecture = 'amd64'
        elif platform.machine() == 'aarch64':
            architecture = 'arm64'
        else:
            architecture = platform.machine()

    # 创建临时目录结构
    pkg_name = f"{app_name.lower()}_{app_version}_{architecture}"
    pkg_root = f"build/{pkg_name}"

    # 创建目录结构
    os.makedirs(f"{pkg_root}/DEBIAN", exist_ok=True)
    os.makedirs(f"{pkg_root}/usr/bin", exist_ok=True)
    os.makedirs(f"{pkg_root}/usr/share/applications", exist_ok=True)
    os.makedirs(f"{pkg_root}/usr/share/{app_name.lower()}", exist_ok=True)
    os.makedirs(
        f"{pkg_root}/usr/share/icons/hicolor/256x256/apps", exist_ok=True)

    # 创建control文件
    control_content = f"""Package: {app_name.lower()}
Version: {app_version}
Architecture: {architecture}
Maintainer: {maintainer}
Description: {app_description}
"""

    if dependencies:
        control_content += f"Depends: {', '.join(dependencies)}\n"

    with open(f"{pkg_root}/DEBIAN/control", "w") as f:
        f.write(control_content)

    # 复制应用程序文件
    try:
        if os.path.isdir(source_dir):
            # 复制目录内容到usr/share/{app_name}
            for item in os.listdir(source_dir):
                src = os.path.join(source_dir, item)
                dst = os.path.join(
                    f"{pkg_root}/usr/share/{app_name.lower()}", item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)

            # 创建可执行文件链接
            exec_path = os.path.join(
                f"/usr/share/{app_name.lower()}", app_name)
            with open(f"{pkg_root}/usr/bin/{app_name.lower()}", "w") as f:
                f.write(f"""#!/bin/sh
exec {exec_path} "$@"
""")
            os.chmod(f"{pkg_root}/usr/bin/{app_name.lower()}", 0o755)

            # 查找并复制图标
            icon_files = glob.glob(
                f"{source_dir}/*.png") + glob.glob(f"{source_dir}/*.svg")
            if icon_files:
                icon_file = icon_files[0]
                icon_name = os.path.basename(icon_file)
                shutil.copy2(
                    icon_file, f"{pkg_root}/usr/share/icons/hicolor/256x256/apps/{icon_name}")

                # 创建桌面入口文件
                desktop_content = create_desktop_entry(
                    app_name,
                    f"/usr/bin/{app_name.lower()}",
                    f"/usr/share/icons/hicolor/256x256/apps/{icon_name}",
                    app_description
                )

                with open(f"{pkg_root}/usr/share/applications/{app_name.lower()}.desktop", "w") as f:
                    f.write(desktop_content)

            # 构建.deb包
            try:
                deb_cmd = ["dpkg-deb", "--build",
                           "--root-owner-group", pkg_root]
                print(f"执行命令: {' '.join(deb_cmd)}")
                subprocess.run(deb_cmd, check=True)

                # 移动.deb包到当前目录
                deb_file = f"{pkg_name}.deb"
                if os.path.exists(f"build/{deb_file}"):
                    shutil.move(f"build/{deb_file}", deb_file)
                    print(f"Debian包创建成功: {deb_file}")
                    return os.path.abspath(deb_file)
                else:
                    print(f"错误: 未找到生成的.deb文件")
                    return None
            except subprocess.CalledProcessError as e:
                print(f"Debian包构建失败: {e}")
                return None
        else:
            print(f"错误: 源目录不存在或不是目录: {source_dir}")
            return None
    except Exception as e:
        print(f"创建Debian包时发生错误: {e}")
        return None


def create_rpm_package(app_name, app_version, app_description, maintainer,
                       source_dir, requires=None):
    """
    创建RPM软件包(.rpm)

    Args:
        app_name: 应用程序名称
        app_version: 应用程序版本
        app_description: 应用程序描述
        maintainer: 维护者信息
        source_dir: 源文件目录
        requires: 依赖包列表

    Returns:
        str: 生成的.rpm文件路径
    """
    # 检查是否已安装rpm-build工具
    try:
        subprocess.run(["rpmbuild", "--version"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: rpmbuild未安装，请先安装rpm-build工具包")
        return None

    # 创建RPM构建目录结构
    home_dir = os.path.expanduser("~")
    rpmbuild_dir = os.path.join(home_dir, "rpmbuild")

    for dir_name in ["BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS"]:
        os.makedirs(os.path.join(rpmbuild_dir, dir_name), exist_ok=True)

    # 创建tarball源文件
    source_tarball = f"{app_name.lower()}-{app_version}.tar.gz"
    source_tarball_path = os.path.join(rpmbuild_dir, "SOURCES", source_tarball)

    # 创建临时目录并复制文件
    temp_dir = os.path.join("build", f"{app_name.lower()}-{app_version}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        if os.path.isdir(source_dir):
            for item in os.listdir(source_dir):
                src = os.path.join(source_dir, item)
                dst = os.path.join(temp_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)

            # 创建桌面入口文件和启动脚本
            desktop_content = create_desktop_entry(
                app_name,
                f"/usr/bin/{app_name.lower()}",
                f"/usr/share/icons/hicolor/256x256/apps/{app_name.lower()}.png",
                app_description
            )

            os.makedirs(os.path.join(temp_dir, "desktop"), exist_ok=True)
            with open(os.path.join(temp_dir, "desktop", f"{app_name.lower()}.desktop"), "w") as f:
                f.write(desktop_content)

            with open(os.path.join(temp_dir, "startscript.sh"), "w") as f:
                f.write(f"""#!/bin/sh
exec /usr/share/{app_name.lower()}/{app_name} "$@"
""")

            # 创建tarball
            current_dir = os.getcwd()
            os.chdir("build")
            tar_cmd = ["tar", "czf", source_tarball_path,
                       f"{app_name.lower()}-{app_version}"]
            subprocess.run(tar_cmd, check=True)
            os.chdir(current_dir)

            # 创建spec文件
            spec_content = f"""
Name:           {app_name.lower()}
Version:        {app_version}
Release:        1%{{?dist}}
Summary:        {app_description}

License:        Proprietary
URL:            http://example.com
Source0:        %{{name}}-%{{version}}.tar.gz

BuildArch:      {platform.machine()}
"""

            if requires:
                spec_content += f"Requires:       {', '.join(requires)}\n"

            spec_content += f"""
%description
{app_description}

%prep
%setup -q

%install
mkdir -p %{{buildroot}}/usr/share/%{{name}}
mkdir -p %{{buildroot}}/usr/bin
mkdir -p %{{buildroot}}/usr/share/applications
mkdir -p %{{buildroot}}/usr/share/icons/hicolor/256x256/apps

# 复制应用程序文件
cp -r * %{{buildroot}}/usr/share/%{{name}}/

# 安装桌面文件
install -m 0644 desktop/%{{name}}.desktop %{{buildroot}}/usr/share/applications/

# 安装启动脚本
install -m 0755 startscript.sh %{{buildroot}}/usr/bin/%{{name}}

# 查找并安装图标
if [ -f "*.png" ]; then
    install -m 0644 *.png %{{buildroot}}/usr/share/icons/hicolor/256x256/apps/%{{name}}.png
elif [ -f "*.svg" ]; then
    install -m 0644 *.svg %{{buildroot}}/usr/share/icons/hicolor/256x256/apps/%{{name}}.svg
fi

%files
%{{_bindir}}/%{{name}}
%{{_datadir}}/%{{name}}
%{{_datadir}}/applications/%{{name}}.desktop
%{{_datadir}}/icons/hicolor/256x256/apps/%{{name}}.*

%changelog
* {subprocess.check_output(["date", "+%a %b %d %Y"]).decode().strip()} {maintainer} - {app_version}-1
- Initial package
"""

            spec_file_path = os.path.join(
                rpmbuild_dir, "SPECS", f"{app_name.lower()}.spec")
            with open(spec_file_path, "w") as f:
                f.write(spec_content)

            # 构建RPM包
            try:
                rpm_cmd = ["rpmbuild", "-ba", spec_file_path]
                print(f"执行命令: {' '.join(rpm_cmd)}")
                subprocess.run(rpm_cmd, check=True)

                # 查找生成的RPM包
                rpm_files = glob.glob(os.path.join(
                    rpmbuild_dir, "RPMS", "*", f"{app_name.lower()}-{app_version}*.rpm"))
                if rpm_files:
                    rpm_file = rpm_files[0]
                    # 复制RPM包到当前目录
                    output_rpm = os.path.basename(rpm_file)
                    shutil.copy2(rpm_file, output_rpm)
                    print(f"RPM包创建成功: {output_rpm}")
                    return os.path.abspath(output_rpm)
                else:
                    print(f"错误: 未找到生成的RPM文件")
                    return None
            except subprocess.CalledProcessError as e:
                print(f"RPM包构建失败: {e}")
                return None
        else:
            print(f"错误: 源目录不存在或不是目录: {source_dir}")
            return None
    except Exception as e:
        print(f"创建RPM包时发生错误: {e}")
        return None


def create_appimage(app_name, app_version, app_description, source_dir, icon_path=None):
    """
    创建AppImage可执行文件

    Args:
        app_name: 应用程序名称
        app_version: 应用程序版本
        app_description: 应用程序描述
        source_dir: 源文件目录
        icon_path: 图标文件路径

    Returns:
        str: 生成的AppImage文件路径
    """
    # 检查appimagetool是否安装
    appimagetool_path = shutil.which("appimagetool")
    if not appimagetool_path:
        print("错误: 未找到appimagetool，请先安装")
        print("可以从 https://github.com/AppImage/AppImageKit/releases 下载")
        return None

    # 创建AppDir目录结构
    appdir = f"build/{app_name.lower()}.AppDir"
    os.makedirs(f"{appdir}/usr/bin", exist_ok=True)
    os.makedirs(f"{appdir}/usr/share/applications", exist_ok=True)
    os.makedirs(
        f"{appdir}/usr/share/icons/hicolor/256x256/apps", exist_ok=True)

    try:
        if os.path.isdir(source_dir):
            # 复制应用程序文件
            for item in os.listdir(source_dir):
                src = os.path.join(source_dir, item)
                dst = os.path.join(appdir, "usr/bin", item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)

            # 复制图标
            if icon_path and os.path.exists(icon_path):
                icon_ext = os.path.splitext(icon_path)[1]
                icon_dest = f"{appdir}/usr/share/icons/hicolor/256x256/apps/{app_name.lower()}{icon_ext}"
                shutil.copy2(icon_path, icon_dest)

                # 同时复制到AppDir根目录作为AppImage图标
                shutil.copy2(
                    icon_path, f"{appdir}/{app_name.lower()}{icon_ext}")
            else:
                # 查找可能的图标文件
                icon_files = glob.glob(
                    f"{source_dir}/*.png") + glob.glob(f"{source_dir}/*.svg")
                if icon_files:
                    icon_file = icon_files[0]
                    icon_ext = os.path.splitext(icon_file)[1]
                    shutil.copy2(
                        icon_file, f"{appdir}/usr/share/icons/hicolor/256x256/apps/{app_name.lower()}{icon_ext}")
                    shutil.copy2(
                        icon_file, f"{appdir}/{app_name.lower()}{icon_ext}")

            # 创建desktop文件
            desktop_content = create_desktop_entry(
                app_name,
                f"{app_name.lower()}",
                f"{app_name.lower()}",
                app_description
            )

            with open(f"{appdir}/usr/share/applications/{app_name.lower()}.desktop", "w") as f:
                f.write(desktop_content)

            # 复制desktop文件到AppDir根目录
            shutil.copy2(f"{appdir}/usr/share/applications/{app_name.lower()}.desktop",
                         f"{appdir}/{app_name.lower()}.desktop")

            # 创建AppRun文件
            with open(f"{appdir}/AppRun", "w") as f:
                f.write("""#!/bin/sh
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${HERE}/usr/sbin:${HERE}/usr/games:${HERE}/bin:${HERE}/sbin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${HERE}/usr/lib/x86_64-linux-gnu:${HERE}/usr/lib/i386-linux-gnu:${HERE}/lib/x86_64-linux-gnu:${HERE}/lib/i386-linux-gnu:${HERE}/lib:${LD_LIBRARY_PATH}"
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS}"
EXEC=$(grep -e '^Exec=.*' "${HERE}"/*.desktop | head -n 1 | cut -d "=" -f 2 | cut -d " " -f 1)
exec "${HERE}/usr/bin/${EXEC}" "$@"
""")
            os.chmod(f"{appdir}/AppRun", 0o755)

            # 构建AppImage
            try:
                output_name = f"{app_name.lower()}-{app_version}-x86_64.AppImage"
                appimage_cmd = [appimagetool_path, appdir, output_name]
                print(f"执行命令: {' '.join(appimage_cmd)}")
                subprocess.run(appimage_cmd, check=True)

                if os.path.exists(output_name):
                    os.chmod(output_name, 0o755)
                    print(f"AppImage创建成功: {output_name}")
                    return os.path.abspath(output_name)
                else:
                    print(f"错误: 未找到生成的AppImage文件")
                    return None
            except subprocess.CalledProcessError as e:
                print(f"AppImage构建失败: {e}")
                return None
        else:
            print(f"错误: 源目录不存在或不是目录: {source_dir}")
            return None
    except Exception as e:
        print(f"创建AppImage时发生错误: {e}")
        return None


def example_package_workflow():
    """演示完整的Linux打包工作流程示例"""
    # 检查Linux环境
    env_info = check_linux_environment()
    if not env_info:
        print("当前不是Linux环境，无法执行Linux打包示例")
        return

    # 示例配置
    app_name = "ExampleApp"
    app_version = "1.0.0"
    app_description = "示例应用程序"
    maintainer = "Example Maintainer <maintainer@example.com>"
    entry_file = "main.py"

    # 项目路径
    project_dir = os.path.abspath(".")
    dist_dir = os.path.join(project_dir, "dist")

    # 1. 使用PyInstaller构建可执行文件
    print("\n1. 构建Linux可执行文件")
    build_success = build_exe_with_pyinstaller(
        app_name,
        entry_file,
        workdir=project_dir,
        onefile=False,
        windowed=True,
        icon="assets/icon.png",
        additional_args="--add-data assets:assets"
    )

    if not build_success:
        print("构建可执行文件失败，无法继续")
        return

    # 源目录路径
    source_path = os.path.join(dist_dir, app_name)

    # 2. 创建Debian包
    print("\n2. 创建Debian包")
    if shutil.which("dpkg-deb"):
        deb_file = create_debian_package(
            app_name,
            app_version,
            app_description,
            maintainer,
            source_path
        )
        if deb_file:
            print(f"Debian包已创建: {deb_file}")
    else:
        print("未安装dpkg-deb工具，跳过Debian包创建")

    # 3. 创建RPM包
    print("\n3. 创建RPM包")
    if shutil.which("rpmbuild"):
        rpm_file = create_rpm_package(
            app_name,
            app_version,
            app_description,
            maintainer,
            source_path
        )
        if rpm_file:
            print(f"RPM包已创建: {rpm_file}")
    else:
        print("未安装rpmbuild工具，跳过RPM包创建")

    # 4. 创建AppImage
    print("\n4. 创建AppImage")
    if shutil.which("appimagetool"):
        appimage_file = create_appimage(
            app_name,
            app_version,
            app_description,
            source_path,
            icon_path=os.path.join(project_dir, "assets/icon.png")
        )
        if appimage_file:
            print(f"AppImage已创建: {appimage_file}")
    else:
        print("未安装appimagetool工具，跳过AppImage创建")

    print("\n打包流程完成!")
    print(f"可执行文件位于: {source_path}/{app_name}")


if __name__ == "__main__":
    # 运行示例工作流程
    print("这是Linux打包代码示例文件，包含各种打包功能的函数")
    print("要查看完整工作流程示例，请调用example_package_workflow()函数")
