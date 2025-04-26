"""
macOS应用打包代码示例

本文件包含用于在macOS平台上打包Python应用的代码示例，
展示如何使用Python脚本处理macOS应用程序包(.app)、
创建DMG镜像文件以及处理代码签名等功能。
"""

import os
import subprocess
import shutil
import plistlib


def create_app_bundle(app_path, executable_path, icon_path=None,
                      bundle_identifier=None):
    """
    创建macOS应用程序包结构

    Args:
        app_path: 应用程序包路径 (.app)
        executable_path: 可执行文件路径
        icon_path: 图标文件路径 (.icns)
        bundle_identifier: 应用标识符
    """
    # 创建应用程序包结构
    contents_dir = os.path.join(app_path, "Contents")
    macos_dir = os.path.join(contents_dir, "MacOS")
    resources_dir = os.path.join(contents_dir, "Resources")

    os.makedirs(macos_dir, exist_ok=True)
    os.makedirs(resources_dir, exist_ok=True)

    # 复制可执行文件
    shutil.copy2(
        executable_path,
        os.path.join(macos_dir, os.path.basename(executable_path))
    )

    # 复制图标文件
    if icon_path and os.path.exists(icon_path):
        shutil.copy2(
            icon_path,
            os.path.join(resources_dir, os.path.basename(icon_path))
        )

    # 创建Info.plist文件
    app_name = os.path.basename(executable_path)

    info_plist = {
        'CFBundleName': app_name,
        'CFBundleDisplayName': app_name,
        'CFBundleIdentifier': bundle_identifier or f"com.example.{app_name}",
        'CFBundleVersion': "1.0.0",
        'CFBundlePackageType': 'APPL',
        'CFBundleExecutable': app_name,
        'NSHighResolutionCapable': True,
    }

    if icon_path:
        info_plist['CFBundleIconFile'] = os.path.basename(icon_path)

    # 写入Info.plist
    with open(os.path.join(contents_dir, "Info.plist"), 'wb') as f:
        plistlib.dump(info_plist, f)

    print(f"应用程序包已创建: {app_path}")


def sign_app_bundle(app_path, identity, entitlements_path=None):
    """
    对macOS应用程序包进行代码签名

    Args:
        app_path: 应用程序包路径 (.app)
        identity: 签名身份（证书）
        entitlements_path: 授权文件路径

    Returns:
        bool: 签名是否成功
    """
    print(f"正在对应用进行签名: {app_path}")

    # 构建签名命令
    cmd = ['codesign', '--force', '--sign', identity]

    if entitlements_path:
        cmd.extend(['--entitlements', entitlements_path])

    cmd.extend(['--deep', '--timestamp', app_path])

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("签名成功!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"签名失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def create_dmg(app_path, dmg_path, volume_name):
    """
    创建DMG安装镜像

    Args:
        app_path: 应用程序包路径 (.app)
        dmg_path: 输出DMG文件路径
        volume_name: 卷标名称

    Returns:
        bool: 创建是否成功
    """
    print(f"正在创建DMG镜像: {dmg_path}")

    try:
        # 检查是否安装了create-dmg
        subprocess.run(
            ['which', 'create-dmg'],
            check=True,
            capture_output=True
        )

        # 构建create-dmg命令
        cmd = [
            'create-dmg',
            '--volname', volume_name,
            '--window-pos', '200', '100',
            '--window-size', '800', '400',
            '--icon-size', '100',
            '--app-drop-link', '600', '185',
            '--icon', os.path.basename(app_path), '200', '185',
            '--hide-extension', os.path.basename(app_path),
            '--no-internet-enable',
            dmg_path,
            app_path
        ]

        subprocess.run(cmd, check=True)
        print(f"DMG镜像创建成功: {dmg_path}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"创建DMG失败: {e}")

        # 如果create-dmg失败，使用hdiutil作为备选方案
        try:
            temp_dmg = f"{dmg_path}.temp.dmg"

            # 创建临时DMG
            subprocess.run([
                'hdiutil', 'create',
                '-srcfolder', os.path.dirname(app_path),
                '-volname', volume_name,
                '-format', 'UDRW',
                temp_dmg
            ], check=True)

            # 转换为压缩格式
            subprocess.run([
                'hdiutil', 'convert',
                temp_dmg,
                '-format', 'UDZO',
                '-o', dmg_path
            ], check=True)

            # 清理临时文件
            os.remove(temp_dmg)

            print(f"使用hdiutil创建DMG成功: {dmg_path}")
            return True

        except subprocess.CalledProcessError as e2:
            print(f"使用hdiutil创建DMG也失败: {e2}")
            return False


def create_zip_archive(app_path, zip_path):
    """
    创建ZIP压缩包作为DMG的替代方案

    Args:
        app_path: 应用程序包路径 (.app)
        zip_path: 输出ZIP文件路径

    Returns:
        bool: 创建是否成功
    """
    print(f"正在创建ZIP压缩包: {zip_path}")

    try:
        # 使用ditto创建ZIP (保留macOS文件元数据)
        subprocess.run([
            'ditto',
            '-c',
            '-k',
            '--keepParent',
            app_path,
            zip_path
        ], check=True)

        print(f"ZIP压缩包创建成功: {zip_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"创建ZIP失败: {e}")

        # 如果ditto失败，使用Python的zipfile作为备选方案
        try:
            shutil.make_archive(
                os.path.splitext(zip_path)[0],  # 基本路径名
                'zip',                          # 格式
                os.path.dirname(app_path),      # 根目录
                os.path.basename(app_path)      # 要打包的目录
            )
            print(f"使用Python创建ZIP成功: {zip_path}")
            return True
        except Exception as e2:
            print(f"使用Python创建ZIP也失败: {e2}")
            return False


def notarize_app(dmg_path, bundle_identifier, username, password):
    """
    对应用进行公证

    Args:
        dmg_path: DMG文件路径
        bundle_identifier: 应用标识符
        username: Apple ID
        password: 应用专用密码

    Returns:
        str: 请求UUID (成功时) 或 None (失败时)
    """
    print(f"正在提交应用公证: {dmg_path}")

    try:
        # 提交公证请求
        cmd = [
            'xcrun', 'altool',
            '--notarize-app',
            '--primary-bundle-id', bundle_identifier,
            '--username', username,
            '--password', password,
            '--file', dmg_path
        ]

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        # 从输出中提取UUID
        for line in result.stdout.split('\n'):
            if "RequestUUID" in line:
                request_uuid = line.split('=')[1].strip()
                print(f"公证请求已提交，UUID: {request_uuid}")
                return request_uuid

        print("公证请求已提交，但无法提取UUID")
        return None

    except subprocess.CalledProcessError as e:
        print(f"提交公证失败: {e}")
        print(f"错误输出: {e.stderr}")
        return None


def check_notarization_status(request_uuid, username, password):
    """
    检查公证状态

    Args:
        request_uuid: 公证请求UUID
        username: Apple ID
        password: 应用专用密码

    Returns:
        str: 公证状态 ("success", "in-progress", "failed", 或 "unknown")
    """
    if not request_uuid:
        return "unknown"

    try:
        cmd = [
            'xcrun', 'altool',
            '--notarization-info', request_uuid,
            '--username', username,
            '--password', password
        ]

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        # 解析输出
        status = "unknown"
        log_url = None

        for line in result.stdout.split('\n'):
            if "Status:" in line:
                status_text = line.split(':')[1].strip()
                if "success" in status_text.lower():
                    status = "success"
                elif "in progress" in status_text.lower():
                    status = "in-progress"
                elif "failed" in status_text.lower():
                    status = "failed"

            if "LogFileURL:" in line:
                log_url = line.split(':')[1].strip()

        print(f"公证状态: {status}")
        if log_url:
            print(f"日志URL: {log_url}")

        return status

    except subprocess.CalledProcessError as e:
        print(f"检查公证状态失败: {e}")
        print(f"错误输出: {e.stderr}")
        return "unknown"


def staple_notarization(app_path):
    """
    给应用添加公证标记

    Args:
        app_path: 应用路径 (.app或.dmg)

    Returns:
        bool: 添加标记是否成功
    """
    print(f"正在给应用添加公证标记: {app_path}")

    try:
        subprocess.run(
            ['xcrun', 'stapler', 'staple', app_path],
            check=True,
            capture_output=True,
            text=True
        )
        print("添加公证标记成功!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"添加公证标记失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def verify_signature(app_path):
    """
    验证应用签名

    Args:
        app_path: 应用路径 (.app)

    Returns:
        bool: 签名是否有效
    """
    print(f"正在验证应用签名: {app_path}")

    try:
        result = subprocess.run(
            ['codesign', '--verify', '--verbose', app_path],
            check=True,
            capture_output=True,
            text=True
        )
        print("应用签名有效!")

        # 显示详细信息
        print("\n签名详细信息:")
        info_result = subprocess.run(
            ['codesign', '--display', '--verbose=4', app_path],
            check=True,
            capture_output=True,
            text=True
        )
        print(info_result.stdout)

        return True
    except subprocess.CalledProcessError as e:
        print(f"应用签名无效: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def example_package_workflow():
    """演示完整的macOS打包工作流程示例"""
    # 示例路径
    app_name = "ExampleApp"
    app_path = f"/path/to/dist/{app_name}.app"
    dmg_path = f"/path/to/installer/{app_name}-1.0.0.dmg"
    icon_path = "/path/to/assets/icon.icns"

    # 假设PyInstaller已经构建了基本的.app包
    print("1. 假设PyInstaller已经创建了基本的.app包")

    # 修正.app包中的Info.plist (如果需要)
    print("\n2. 修正Info.plist文件")
    contents_dir = os.path.join(app_path, "Contents")
    info_plist_path = os.path.join(contents_dir, "Info.plist")

    # 读取现有的Info.plist
    with open(info_plist_path, 'rb') as f:
        info = plistlib.load(f)

    # 修改或添加键值
    info['CFBundleIdentifier'] = "com.example.exampleapp"
    info['CFBundleShortVersionString'] = "1.0.0"
    info['NSHighResolutionCapable'] = True

    # 保存修改后的Info.plist
    with open(info_plist_path, 'wb') as f:
        plistlib.dump(info, f)

    # 签名应用
    print("\n3. 对应用进行签名")
    entitlements_path = "/path/to/entitlements.plist"
    sign_app_bundle(
        app_path, "Developer ID Application: Your Name", entitlements_path)

    # 创建DMG
    print("\n4. 创建DMG安装镜像")
    create_dmg(app_path, dmg_path, "Example App Installer")

    # 提交公证
    print("\n5. 提交应用公证")
    bundle_id = "com.example.exampleapp"
    username = "your.email@example.com"
    password = "your-app-specific-password"

    request_uuid = notarize_app(dmg_path, bundle_id, username, password)

    # 检查公证状态 (实际场景中可能需要循环检查直到完成)
    if request_uuid:
        print("\n6. 检查公证状态")
        status = check_notarization_status(request_uuid, username, password)

        if status == "success":
            # 给DMG添加公证标记
            print("\n7. 给DMG添加公证标记")
            staple_notarization(dmg_path)

            # 验证结果
            print("\n8. 验证最终结果")
            verify_signature(dmg_path)
            print(f"\n打包完成! DMG文件位于: {dmg_path}")
        else:
            print(f"公证尚未完成，状态: {status}")
            print("实际场景中应等待公证完成")
    else:
        print("公证请求失败，检查上面的错误信息")


if __name__ == "__main__":
    # 运行示例工作流程
    print("这是macOS打包代码示例文件，包含各种打包功能的函数")
    print("要查看完整工作流程示例，请调用example_package_workflow()函数")
