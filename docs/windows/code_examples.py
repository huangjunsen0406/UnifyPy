"""
Windows应用打包代码示例

本文件包含用于在Windows平台上打包Python应用的代码示例，
展示如何使用Python脚本调用PyInstaller、创建Windows安装程序
以及处理Windows特有的打包问题。
"""

import os
import sys
import subprocess
import shutil
import winreg
import json
from pathlib import Path


def find_inno_setup():
    """
    查找Windows系统上安装的Inno Setup路径

    优先级:
    1. 环境变量 INNO_SETUP_PATH
    2. 注册表中的安装路径
    3. 常见的默认安装位置

    Returns:
        str: Inno Setup的安装路径，如果未找到则返回None
    """
    # 从环境变量中获取
    inno_path = os.environ.get("INNO_SETUP_PATH")
    if inno_path and os.path.exists(inno_path):
        return inno_path

    # 从注册表中查找
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1") as key:
            inno_path = winreg.QueryValueEx(key, "InstallLocation")[0]
            if os.path.exists(inno_path):
                return inno_path
    except WindowsError:
        pass

    # 检查常见的安装位置
    common_paths = [
        r"C:\Program Files\Inno Setup 6",
        r"C:\Program Files (x86)\Inno Setup 6",
        r"C:\Program Files\Inno Setup 5",
        r"C:\Program Files (x86)\Inno Setup 5"
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    return None


def create_inno_setup_script(app_name, app_version, app_publisher, source_path,
                             output_path, icon_path=None, license_file=None,
                             create_desktop_icon=True, languages=None,
                             requires_admin=False):
    """
    创建Inno Setup脚本

    Args:
        app_name: 应用名称
        app_version: 应用版本
        app_publisher: 发布者
        source_path: 源文件路径 (PyInstaller输出目录)
        output_path: 安装程序输出路径
        icon_path: 图标文件路径
        license_file: 许可证文件路径
        create_desktop_icon: 是否创建桌面图标
        languages: 支持的语言列表
        requires_admin: 是否需要管理员权限安装

    Returns:
        str: 生成的脚本内容
    """
    # 转换为绝对路径
    source_path = os.path.abspath(source_path)
    output_path = os.path.abspath(output_path)

    if icon_path:
        icon_path = os.path.abspath(icon_path)

    if license_file:
        license_file = os.path.abspath(license_file)

    # 设置默认语言
    if not languages:
        languages = ["english"]

    # 开始构建脚本
    script = [
        "[Setup]",
        f'AppName={app_name}',
        f'AppVersion={app_version}',
        f'AppPublisher={app_publisher}',
        f'DefaultDirName={{{app.DefaultProgramFiles}}}\\{app_name}',
        f'DefaultGroupName={app_name}',
        f'OutputDir={output_path}',
        f'OutputBaseFilename={app_name}-{app_version}-setup',
        f'Compression=lzma',
        f'SolidCompression=yes',
    ]

    # 添加图标
    if icon_path:
        script.append(f'SetupIconFile={icon_path}')

    # 添加管理员权限要求
    if requires_admin:
        script.append('PrivilegesRequired=admin')
    else:
        script.append('PrivilegesRequired=lowest')

    # 添加语言支持
    script.append("\n[Languages]")
    for lang in languages:
        if lang.lower() == "english":
            script.append(
                'Name: "english"; MessagesFile: "compiler:Default.isl"')
        elif lang.lower() == "chinesesimp" or lang.lower() == "chinesesimplified":
            script.append(
                'Name: "chinesesimplified"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"')
        elif lang.lower() == "french":
            script.append(
                'Name: "french"; MessagesFile: "compiler:Languages\\French.isl"')
        elif lang.lower() == "german":
            script.append(
                'Name: "german"; MessagesFile: "compiler:Languages\\German.isl"')
        # 可以继续添加其他语言

    # 添加许可证
    if license_file:
        script.append("\n[LicenseFile]")
        script.append(f'Source: "{license_file}"; DestDir: "{{app}}"')

    # 文件部分
    script.append("\n[Files]")
    script.append(
        f'Source: "{source_path}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs')

    # 图标部分
    script.append("\n[Icons]")
    script.append(
        f'Name: "{{group}}\\{app_name}"; Filename: "{{app}}\\{app_name}.exe"')
    script.append(
        f'Name: "{{group}}\\卸载 {app_name}"; Filename: "{{uninstallexe}}"')

    if create_desktop_icon:
        script.append(
            f'Name: "{{commondesktop}}\\{app_name}"; Filename: "{{app}}\\{app_name}.exe"')

    # 运行部分
    script.append("\n[Run]")
    script.append(
        f'Filename: "{{app}}\\{app_name}.exe"; Description: "启动 {app_name}"; Flags: nowait postinstall skipifsilent')

    return "\n".join(script)


def build_exe_with_pyinstaller(app_name, entry_file, workdir=None, onefile=False,
                               windowed=True, icon=None, additional_args=None):
    """
    使用PyInstaller构建Windows可执行文件

    Args:
        app_name: 应用名称
        entry_file: 入口Python文件
        workdir: 工作目录
        onefile: 是否打包为单文件
        windowed: 是否使用无控制台窗口模式
        icon: 图标文件路径
        additional_args: 其他PyInstaller参数

    Returns:
        bool: 是否构建成功
    """
    if workdir:
        os.chdir(workdir)

    # 构建PyInstaller命令
    cmd = ["pyinstaller"]

    # 添加应用名称
    cmd.extend(["--name", app_name])

    # 添加单文件/目录模式
    if onefile:
        cmd.append("--onefile")

    # 添加窗口模式
    if windowed:
        cmd.append("--windowed")

    # 添加图标
    if icon:
        cmd.extend(["--icon", icon])

    # 添加其他参数
    if additional_args:
        cmd.extend(additional_args.split())

    # 添加入口文件
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


def build_inno_setup(script_path, inno_setup_path=None):
    """
    使用Inno Setup构建Windows安装程序

    Args:
        script_path: Inno Setup脚本路径
        inno_setup_path: Inno Setup安装路径

    Returns:
        bool: 是否构建成功
    """
    if not inno_setup_path:
        inno_setup_path = find_inno_setup()
        if not inno_setup_path:
            print("错误: 未找到Inno Setup安装路径")
            return False

    iscc_path = os.path.join(inno_setup_path, "ISCC.exe")
    if not os.path.exists(iscc_path):
        print(f"错误: 找不到ISCC.exe: {iscc_path}")
        return False

    # 执行Inno Setup编译器
    try:
        cmd = [iscc_path, script_path]
        print(f"执行命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        print(f"安装程序构建成功: {script_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"安装程序构建失败: {e}")
        return False


def sign_windows_executable(exe_path, cert_path, cert_password=None):
    """
    对Windows可执行文件进行签名

    Args:
        exe_path: 可执行文件路径
        cert_path: 证书文件路径
        cert_password: 证书密码

    Returns:
        bool: 是否签名成功
    """
    try:
        # 检查是否安装了signtool
        signtool_path = None
        windows_kits_paths = [
            os.path.expandvars(
                r"%ProgramFiles(x86)%\Windows Kits\10\bin\10.0.19041.0\x64"),
            os.path.expandvars(
                r"%ProgramFiles(x86)%\Windows Kits\10\bin\10.0.18362.0\x64"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Windows Kits\10\bin\x64"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Windows Kits\8.1\bin\x64")
        ]

        for path in windows_kits_paths:
            st_path = os.path.join(path, "signtool.exe")
            if os.path.exists(st_path):
                signtool_path = st_path
                break

        if not signtool_path:
            print("错误: 找不到signtool.exe，无法签名")
            return False

        # 构建签名命令
        cmd = [signtool_path, "sign", "/f", cert_path]

        if cert_password:
            cmd.extend(["/p", cert_password])

        cmd.extend(["/t", "http://timestamp.digicert.com", exe_path])

        # 执行签名
        print(f"执行签名命令: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        print(f"签名成功: {exe_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"签名失败: {e}")
        return False


def update_version_info(version_file, version, company_name, file_description,
                        internal_name, original_filename, product_name, trademarks=None):
    """
    创建或更新版本信息文件

    Args:
        version_file: 版本信息文件路径
        version: 版本号 (例如: "1.0.0.0")
        company_name: 公司名称
        file_description: 文件描述
        internal_name: 内部名称
        original_filename: 原始文件名
        product_name: 产品名称
        trademarks: 商标信息

    Returns:
        str: 版本信息文件路径
    """
    # 创建版本信息内容
    version_info = f"""
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers={tuple(map(int, version.split('.')))},
    prodvers={tuple(map(int, version.split('.')))},
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'080404b0',
        [StringStruct(u'CompanyName', u'{company_name}'),
        StringStruct(u'FileDescription', u'{file_description}'),
        StringStruct(u'FileVersion', u'{version}'),
        StringStruct(u'InternalName', u'{internal_name}'),
        StringStruct(u'LegalCopyright', u'Copyright (C) {company_name}'),
        StringStruct(u'OriginalFilename', u'{original_filename}'),
        StringStruct(u'ProductName', u'{product_name}'),
        StringStruct(u'ProductVersion', u'{version}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
"""

    # 写入文件
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(version_info)

    return version_file


def example_package_workflow():
    """演示完整的Windows打包工作流程示例"""
    # 示例配置
    app_name = "ExampleApp"
    app_version = "1.0.0"
    app_publisher = "Example Corp"
    entry_file = "main.py"

    # 项目路径
    project_dir = os.path.abspath(".")
    dist_dir = os.path.join(project_dir, "dist")
    installer_dir = os.path.join(project_dir, "installer")

    # 创建输出目录
    os.makedirs(installer_dir, exist_ok=True)

    # 创建版本信息文件
    version_file = os.path.join(project_dir, "version_info.txt")
    update_version_info(
        version_file,
        "1.0.0.0",
        app_publisher,
        f"{app_name} Application",
        app_name,
        f"{app_name}.exe",
        app_name
    )

    # 1. 使用PyInstaller构建可执行文件
    print("\n1. 构建Windows可执行文件")
    build_success = build_exe_with_pyinstaller(
        app_name,
        entry_file,
        workdir=project_dir,
        onefile=False,
        windowed=True,
        icon="assets/icon.ico",
        additional_args=f"--version-file={version_file} --add-data assets;assets"
    )

    if not build_success:
        print("构建可执行文件失败，无法继续")
        return

    # 2. 创建Inno Setup脚本
    print("\n2. 创建安装程序脚本")
    setup_script_path = os.path.join(project_dir, "setup.iss")

    if os.path.exists(os.path.join(dist_dir, app_name)):
        # 目录模式
        source_path = os.path.join(dist_dir, app_name)
    else:
        # 单文件模式
        source_path = dist_dir

    script_content = create_inno_setup_script(
        app_name,
        app_version,
        app_publisher,
        source_path,
        installer_dir,
        icon_path="assets/icon.ico",
        create_desktop_icon=True,
        languages=["english", "chineseSimplified"]
    )

    with open(setup_script_path, 'w', encoding='utf-8') as f:
        f.write(script_content)

    # 3. 构建安装程序
    print("\n3. 构建Windows安装程序")
    inno_setup_path = find_inno_setup()
    if not inno_setup_path:
        print("未找到Inno Setup，安装程序构建失败")
    else:
        build_inno_setup(setup_script_path, inno_setup_path)

    # 4. 可选：签名可执行文件
    # 注意：需要有有效的代码签名证书
    # sign_windows_executable(
    #     os.path.join(source_path, f"{app_name}.exe"),
    #     "path/to/certificate.pfx",
    #     "certificate_password"
    # )

    print("\n打包流程完成!")
    print(f"可执行文件位于: {source_path}\\{app_name}.exe")
    print(f"安装程序位于: {installer_dir}\\{app_name}-{app_version}-setup.exe")


if __name__ == "__main__":
    # 运行示例工作流程
    print("这是Windows打包代码示例文件，包含各种打包功能的函数")
    print("要查看完整工作流程示例，请调用example_package_workflow()函数")
