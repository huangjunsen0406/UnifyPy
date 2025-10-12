# UnifyPy 高级配置参考

UnifyPy 支持所有底层工具的原生配置项。配置项直接映射到对应工具的参数，因此你可以参考各工具的官方文档来使用高级功能。

## 📘 PyInstaller 高级配置

UnifyPy 的 `pyinstaller` 配置节中的所有选项都会直接转换为 PyInstaller 的命令行参数。

### 常用高级配置

| 配置项 | 类型 | 说明 | PyInstaller 参数 | 使用场景 |
|--------|------|------|-----------------|---------|
| `hidden_import` | array | 手动指定隐藏导入的模块 | `--hidden-import` | 动态导入、插件系统、条件加载 |
| `exclude_module` | array | 排除不需要的模块 | `--exclude-module` | 减小包体积，排除如 tkinter, matplotlib 等大型库 |
| `runtime_hook` | array | 运行时钩子脚本路径 | `--runtime-hook` | 程序启动前执行的 Python 脚本，用于环境设置 |
| `splash` | string | 启动画面图片路径 | `--splash` | 应用启动时显示图片（需 PyInstaller 4.1+） |
| `collect_submodules` | array | 收集某包的所有子模块 | `--collect-submodules` | 批量包含复杂库的所有子模块 |
| `collect_data` | array | 收集某包的数据文件 | `--collect-data` | 包含库的资源文件 |
| `collect_all` | array | 收集某包的所有内容 | `--collect-all` | 最完整的收集方式，适合复杂第三方库 |
| `upx_exclude` | array | 排除 UPX 压缩的文件 | `--upx-exclude` | 某些 DLL/SO 压缩后无法运行时使用 |
| `optimize` | integer | Python 优化级别 (0-2) | `-O` | 0=不优化, 1=移除断言, 2=移除文档字符串 |
| `strip` | boolean | 剥离调试符号 | `--strip` | 减小可执行文件大小（Linux/macOS） |
| `key` | string | 字节码加密密钥 | `--key` | 基本的代码保护（⚠️ 非强加密） |

### 示例配置

```json
{
  "pyinstaller": {
    "onefile": false,
    "windowed": true,

    "hidden_import": [
      "requests",
      "PIL.Image",
      "numpy.core._dtype_ctypes"
    ],

    "exclude_module": [
      "tkinter",
      "matplotlib",
      "pandas",
      "scipy"
    ],

    "collect_all": ["torch", "tensorflow"],

    "runtime_hook": ["hooks/runtime_hook.py"],

    "splash": "assets/splash.png",

    "upx_exclude": [
      "vcruntime*.dll",
      "python*.dll",
      "*.dylib"
    ],

    "optimize": 2,
    "strip": true
  }
}
```

### macOS 特定 PyInstaller 配置

| 配置项 | 类型 | 说明 | 使用场景 |
|--------|------|------|---------|
| `target_architecture` | string | 目标架构 | `x86_64`, `arm64`, `universal2`（支持 Apple Silicon） |
| `codesign_identity` | string | 代码签名证书 | 商业发布、公证认证 |
| `osx_entitlements_file` | string | 自定义权限文件路径 | 需要特殊权限配置时 |

**示例**：

```json
{
  "pyinstaller": {
    "target_architecture": "universal2",
    "codesign_identity": "Developer ID Application: Company Name (TEAM_ID)",
    "osx_entitlements_file": "custom_entitlements.plist"
  }
}
```

### Windows 特定 PyInstaller 配置

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `version_file` | string | Windows 版本信息文件 |
| `manifest` | string | Windows 应用清单文件 |
| `uac_admin` | boolean | 需要管理员权限 |
| `uac_uiaccess` | boolean | UI 自动化访问 |

### 官方文档

- 📖 **PyInstaller 完整文档**: https://pyinstaller.org/en/stable/usage.html
- 📖 **所有命令行选项**: https://pyinstaller.org/en/stable/usage.html#options
- 📖 **运行时钩子**: https://pyinstaller.org/en/stable/hooks.html

---

## 🪟 Windows 高级配置

### Inno Setup 配置

UnifyPy 的 `windows.inno_setup` 配置会转换为 Inno Setup 脚本（.iss 文件）。

#### 常用高级配置

| 配置项 | 类型 | 说明 | Inno Setup 字段 |
|--------|------|------|----------------|
| `app_id` | string | 应用唯一标识（GUID） | `[Setup] AppId` |
| `app_url` | string | 应用主页 | `[Setup] AppPublisherURL` |
| `app_support_url` | string | 技术支持页面 | `[Setup] AppSupportURL` |
| `license_file` | string | 许可证文件路径 | `[Setup] LicenseFile` |
| `setup_icon` | string | 安装程序图标 | `[Setup] SetupIconFile` |
| `compression` | string | 压缩算法 | `[Setup] Compression` |
| `solid_compression` | boolean | 固实压缩 | `[Setup] SolidCompression` |
| `require_admin` | boolean | 需要管理员权限 | `[Setup] PrivilegesRequired` |
| `wizard_style` | string | 向导样式 | `[Setup] WizardStyle` |
| `uninstall_display_name` | string | 卸载程序显示名称 | `[Setup] UninstallDisplayName` |

#### 示例配置

```json
{
  "windows": {
    "inno_setup": {
      "app_id": "{A1B2C3D4-E5F6-7890-ABCD-123456789012}",
      "app_url": "https://example.com",
      "app_support_url": "https://example.com/support",
      "license_file": "LICENSE.txt",
      "setup_icon": "assets/installer.ico",
      "compression": "lzma2",
      "solid_compression": true,
      "require_admin": false,
      "wizard_style": "modern",
      "languages": ["english", "chinesesimplified"],
      "create_desktop_icon": true,
      "create_start_menu_icon": true
    }
  }
}
```

#### 可用语言代码

| 代码 | 语言 |
|------|------|
| `english` | English |
| `chinesesimplified` | 简体中文 |
| `chinesetraditional` | 繁體中文 |
| `japanese` | 日本語 |
| `korean` | 한국어 |
| `french` | Français |
| `german` | Deutsch |
| `spanish` | Español |

### 官方文档

- 📖 **Inno Setup 完整文档**: https://jrsoftware.org/ishelp/
- 📖 **[Setup] 节配置**: https://jrsoftware.org/ishelp/index.php?topic=setupsection
- 📖 **[Tasks] 节配置**: https://jrsoftware.org/ishelp/index.php?topic=taskssection
- 📖 **[Languages] 节配置**: https://jrsoftware.org/ishelp/index.php?topic=languagessection

---

## 🍎 macOS 高级配置

### Info.plist 配置

UnifyPy 的 `platforms.macos` 配置会更新生成的 .app 包中的 Info.plist 文件。

#### 常用配置

| 配置项 | 类型 | 说明 | Info.plist Key |
|--------|------|------|---------------|
| `bundle_identifier` | string | Bundle ID（必需） | `CFBundleIdentifier` |
| `minimum_system_version` | string | 最低系统版本 | `LSMinimumSystemVersion` |
| `category` | string | 应用分类 | `LSApplicationCategoryType` |
| `high_resolution_capable` | boolean | 支持 Retina 显示 | `NSHighResolutionCapable` |
| `supports_automatic_graphics_switching` | boolean | 支持自动切换显卡 | `NSSupportsAutomaticGraphicsSwitching` |

#### 权限配置

所有以 `_usage_description` 结尾的配置项都会添加到 Info.plist 中。完整权限列表见 [交互式向导文档](../README.md#4️⃣-macos-平台配置如果选择了-macos)。

**示例**：

```json
{
  "macos": {
    "microphone_usage_description": "需要访问麦克风进行录音",
    "camera_usage_description": "需要访问摄像头进行拍照",
    "location_usage_description": "需要访问位置信息提供服务"
  }
}
```

### DMG 配置

UnifyPy 的 `platforms.macos.dmg` 配置会传递给 create-dmg 工具。

#### 常用配置

| 配置项 | 类型 | 说明 | create-dmg 参数 |
|--------|------|------|----------------|
| `volname` | string | 磁盘映像卷名 | `--volname` |
| `window_size` | array | 窗口大小 [宽, 高] | `--window-size` |
| `icon_size` | integer | 图标大小 | `--icon-size` |
| `background` | string | 背景图片路径 | `--background` |
| `format` | string | 磁盘格式 | `--format` |
| `eula` | string | 许可协议文件 | `--eula` |

### 官方文档

- 📖 **Apple Info.plist 参考**: https://developer.apple.com/documentation/bundleresources/information_property_list
- 📖 **macOS 权限列表**: https://developer.apple.com/documentation/bundleresources/information_property_list/protected_resources
- 📖 **代码签名指南**: https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution
- 📖 **create-dmg 文档**: https://github.com/create-dmg/create-dmg

---

## 🐧 Linux 高级配置

### DEB 包配置

UnifyPy 的 `platforms.linux.deb` 配置会生成 DEBIAN/control 文件。

#### 常用配置

| 配置项 | 类型 | 说明 | control 字段 |
|--------|------|------|-------------|
| `package` | string | 包名（必需） | `Package` |
| `maintainer` | string | 维护者信息 | `Maintainer` |
| `depends` | array | 依赖包列表 | `Depends` |
| `recommends` | array | 推荐包列表 | `Recommends` |
| `suggests` | array | 建议包列表 | `Suggests` |
| `section` | string | 软件分类 | `Section` |
| `priority` | string | 优先级 | `Priority` |
| `description` | string | 简短描述 | `Description` |
| `long_description` | string | 详细描述 | `Description`（多行） |
| `postinst_script` | string | 安装后脚本 | `postinst` 文件 |
| `prerm_script` | string | 卸载前脚本 | `prerm` 文件 |
| `postrm_script` | string | 卸载后脚本 | `postrm` 文件 |

#### 示例配置

```json
{
  "linux": {
    "deb": {
      "package": "myapp",
      "maintainer": "Developer <dev@example.com>",
      "depends": [
        "python3 (>= 3.8)",
        "python3-pip",
        "libgtk-3-0"
      ],
      "recommends": ["git", "curl"],
      "section": "utils",
      "priority": "optional",
      "description": "我的应用程序",
      "postinst_script": "#!/bin/bash\necho '安装完成'\nldconfig"
    }
  }
}
```

### RPM 包配置

UnifyPy 的 `platforms.linux.rpm` 配置会生成 RPM spec 文件。

#### 常用配置

| 配置项 | 类型 | 说明 | spec 文件字段 |
|--------|------|------|--------------|
| `name` | string | 包名（必需） | `Name` |
| `summary` | string | 简短摘要 | `Summary` |
| `license` | string | 许可证 | `License` |
| `url` | string | 项目主页 | `URL` |
| `requires` | array | 依赖包列表 | `Requires` |
| `build_requires` | array | 编译依赖 | `BuildRequires` |
| `group` | string | 软件组 | `Group` |
| `description` | string | 详细描述 | `%description` |
| `post_script` | string | 安装后脚本 | `%post` |
| `preun_script` | string | 卸载前脚本 | `%preun` |
| `postun_script` | string | 卸载后脚本 | `%postun` |

#### 示例配置

```json
{
  "linux": {
    "rpm": {
      "name": "myapp",
      "summary": "我的应用程序",
      "license": "MIT",
      "url": "https://example.com",
      "requires": ["python3 >= 3.8", "python3-pip"],
      "group": "Applications/Utilities",
      "description": "详细的应用描述",
      "post_script": "echo '安装完成'\nldconfig"
    }
  }
}
```

### AppImage 配置

UnifyPy 的 `platforms.linux.appimage` 配置用于生成 AppImage 便携格式。

#### 常用配置

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `desktop_entry` | boolean | 是否生成 .desktop 文件 |
| `categories` | array | 桌面分类 |
| `mime_types` | array | 支持的 MIME 类型 |
| `compression` | string | 压缩算法（gzip/xz） |
| `update_information` | string | 自动更新信息 |

### 官方文档

- 📖 **Debian Policy Manual**: https://www.debian.org/doc/debian-policy/
- 📖 **Debian 控制文件**: https://www.debian.org/doc/debian-policy/ch-controlfields.html
- 📖 **RPM Packaging Guide**: https://rpm-packaging-guide.github.io/
- 📖 **RPM spec 文件格式**: https://rpm-software-management.github.io/rpm/manual/spec.html
- 📖 **AppImage 文档**: https://docs.appimage.org/
- 📖 **Desktop Entry 规范**: https://specifications.freedesktop.org/desktop-entry-spec/latest/

---

## 📝 配置示例文件

项目中提供了多个完整的配置示例供参考：

| 文件 | 说明 |
|------|------|
| `build.json` | 基础配置示例 |
| `build_multiformat.json` | 多格式打包配置示例 |
| `build_comprehensive.json` | **完整功能演示**，包含所有可用配置项 |
| `build_macos_permissions_example.json` | macOS 权限配置详细示例 |

**查看完整配置**：

```bash
# 查看完整配置示例（包含所有高级选项）
cat build_comprehensive.json

# 复制为自己的配置
cp build_comprehensive.json my_build.json
```
