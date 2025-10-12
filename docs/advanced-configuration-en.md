# UnifyPy Advanced Configuration Reference

UnifyPy supports all native configuration items of underlying tools. Configuration items are directly mapped to corresponding tool parameters, so you can refer to official documentation of each tool to use advanced features.

## 📘 PyInstaller Advanced Configuration

All options in UnifyPy's `pyinstaller` configuration section will be directly converted to PyInstaller command-line parameters.

### Common Advanced Configurations

| Configuration | Type | Description | PyInstaller Parameter | Use Case |
|--------------|------|-------------|----------------------|----------|
| `hidden_import` | array | Manually specify hidden imported modules | `--hidden-import` | Dynamic imports, plugin systems, conditional loading |
| `exclude_module` | array | Exclude unnecessary modules | `--exclude-module` | Reduce package size, exclude large libraries like tkinter, matplotlib |
| `runtime_hook` | array | Runtime hook script paths | `--runtime-hook` | Python scripts executed before program starts, for environment setup |
| `splash` | string | Splash screen image path | `--splash` | Display image when application starts (requires PyInstaller 4.1+) |
| `collect_submodules` | array | Collect all submodules of a package | `--collect-submodules` | Batch include all submodules of complex libraries |
| `collect_data` | array | Collect data files of a package | `--collect-data` | Include library resource files |
| `collect_all` | array | Collect all content of a package | `--collect-all` | Most complete collection method, suitable for complex third-party libraries |
| `upx_exclude` | array | Exclude files from UPX compression | `--upx-exclude` | Use when some DLLs/SOs cannot run after compression |
| `optimize` | integer | Python optimization level (0-2) | `-O` | 0=no optimization, 1=remove assertions, 2=remove docstrings |
| `strip` | boolean | Strip debug symbols | `--strip` | Reduce executable file size (Linux/macOS) |
| `key` | string | Bytecode encryption key | `--key` | Basic code protection (⚠️ not strong encryption) |

### Example Configuration

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

### macOS Specific PyInstaller Configuration

| Configuration | Type | Description | Use Case |
|--------------|------|-------------|----------|
| `target_architecture` | string | Target architecture | `x86_64`, `arm64`, `universal2` (supports Apple Silicon) |
| `codesign_identity` | string | Code signing certificate | Commercial release, notarization |
| `osx_entitlements_file` | string | Custom entitlements file path | When special permissions configuration is needed |

**Example**:

```json
{
  "pyinstaller": {
    "target_architecture": "universal2",
    "codesign_identity": "Developer ID Application: Company Name (TEAM_ID)",
    "osx_entitlements_file": "custom_entitlements.plist"
  }
}
```

### Windows Specific PyInstaller Configuration

| Configuration | Type | Description |
|--------------|------|-------------|
| `version_file` | string | Windows version information file |
| `manifest` | string | Windows application manifest file |
| `uac_admin` | boolean | Requires administrator privileges |
| `uac_uiaccess` | boolean | UI automation access |

### Official Documentation

- 📖 **PyInstaller Complete Documentation**: https://pyinstaller.org/en/stable/usage.html
- 📖 **All Command-line Options**: https://pyinstaller.org/en/stable/usage.html#options
- 📖 **Runtime Hooks**: https://pyinstaller.org/en/stable/hooks.html

---

## 🪟 Windows Advanced Configuration

### Inno Setup Configuration

UnifyPy's `windows.inno_setup` configuration will be converted to Inno Setup script (.iss file).

#### Common Advanced Configurations

| Configuration | Type | Description | Inno Setup Field |
|--------------|------|-------------|-----------------|
| `app_id` | string | Application unique identifier (GUID) | `[Setup] AppId` |
| `app_url` | string | Application homepage | `[Setup] AppPublisherURL` |
| `app_support_url` | string | Technical support page | `[Setup] AppSupportURL` |
| `license_file` | string | License file path | `[Setup] LicenseFile` |
| `setup_icon` | string | Installer icon | `[Setup] SetupIconFile` |
| `compression` | string | Compression algorithm | `[Setup] Compression` |
| `solid_compression` | boolean | Solid compression | `[Setup] SolidCompression` |
| `require_admin` | boolean | Requires administrator privileges | `[Setup] PrivilegesRequired` |
| `wizard_style` | string | Wizard style | `[Setup] WizardStyle` |
| `uninstall_display_name` | string | Uninstaller display name | `[Setup] UninstallDisplayName` |

#### Example Configuration

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

#### Available Language Codes

| Code | Language |
|------|----------|
| `english` | English |
| `chinesesimplified` | 简体中文 |
| `chinesetraditional` | 繁體中文 |
| `japanese` | 日本語 |
| `korean` | 한국어 |
| `french` | Français |
| `german` | Deutsch |
| `spanish` | Español |

### Official Documentation

- 📖 **Inno Setup Complete Documentation**: https://jrsoftware.org/ishelp/
- 📖 **[Setup] Section Configuration**: https://jrsoftware.org/ishelp/index.php?topic=setupsection
- 📖 **[Tasks] Section Configuration**: https://jrsoftware.org/ishelp/index.php?topic=taskssection
- 📖 **[Languages] Section Configuration**: https://jrsoftware.org/ishelp/index.php?topic=languagessection

---

## 🍎 macOS Advanced Configuration

### Info.plist Configuration

UnifyPy's `platforms.macos` configuration will update the Info.plist file in the generated .app bundle.

#### Common Configurations

| Configuration | Type | Description | Info.plist Key |
|--------------|------|-------------|---------------|
| `bundle_identifier` | string | Bundle ID (required) | `CFBundleIdentifier` |
| `minimum_system_version` | string | Minimum system version | `LSMinimumSystemVersion` |
| `category` | string | Application category | `LSApplicationCategoryType` |
| `high_resolution_capable` | boolean | Support Retina display | `NSHighResolutionCapable` |
| `supports_automatic_graphics_switching` | boolean | Support automatic graphics switching | `NSSupportsAutomaticGraphicsSwitching` |

#### Permission Configuration

All configuration items ending with `_usage_description` will be added to Info.plist. For complete permission list, see [Interactive Wizard Guide](../README_EN.md#4️⃣-macos-platform-configuration-if-macos-selected).

**Example**:

```json
{
  "macos": {
    "microphone_usage_description": "Microphone access required for recording",
    "camera_usage_description": "Camera access required for photography",
    "location_usage_description": "Location access required to provide services"
  }
}
```

### DMG Configuration

UnifyPy's `platforms.macos.dmg` configuration will be passed to the create-dmg tool.

#### Common Configurations

| Configuration | Type | Description | create-dmg Parameter |
|--------------|------|-------------|---------------------|
| `volname` | string | Disk image volume name | `--volname` |
| `window_size` | array | Window size [width, height] | `--window-size` |
| `icon_size` | integer | Icon size | `--icon-size` |
| `background` | string | Background image path | `--background` |
| `format` | string | Disk format | `--format` |
| `eula` | string | License agreement file | `--eula` |

### Official Documentation

- 📖 **Apple Info.plist Reference**: https://developer.apple.com/documentation/bundleresources/information_property_list
- 📖 **macOS Permissions List**: https://developer.apple.com/documentation/bundleresources/information_property_list/protected_resources
- 📖 **Code Signing Guide**: https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution
- 📖 **create-dmg Documentation**: https://github.com/create-dmg/create-dmg

---

## 🐧 Linux Advanced Configuration

### DEB Package Configuration

UnifyPy's `platforms.linux.deb` configuration will generate the DEBIAN/control file.

#### Common Configurations

| Configuration | Type | Description | control Field |
|--------------|------|-------------|--------------|
| `package` | string | Package name (required) | `Package` |
| `maintainer` | string | Maintainer information | `Maintainer` |
| `depends` | array | Dependency package list | `Depends` |
| `recommends` | array | Recommended package list | `Recommends` |
| `suggests` | array | Suggested package list | `Suggests` |
| `section` | string | Software category | `Section` |
| `priority` | string | Priority | `Priority` |
| `description` | string | Brief description | `Description` |
| `long_description` | string | Detailed description | `Description` (multi-line) |
| `postinst_script` | string | Post-installation script | `postinst` file |
| `prerm_script` | string | Pre-uninstallation script | `prerm` file |
| `postrm_script` | string | Post-uninstallation script | `postrm` file |

#### Example Configuration

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
      "description": "My application",
      "postinst_script": "#!/bin/bash\necho 'Installation completed'\nldconfig"
    }
  }
}
```

### RPM Package Configuration

UnifyPy's `platforms.linux.rpm` configuration will generate the RPM spec file.

#### Common Configurations

| Configuration | Type | Description | spec File Field |
|--------------|------|-------------|----------------|
| `name` | string | Package name (required) | `Name` |
| `summary` | string | Brief summary | `Summary` |
| `license` | string | License | `License` |
| `url` | string | Project homepage | `URL` |
| `requires` | array | Dependency package list | `Requires` |
| `build_requires` | array | Build dependencies | `BuildRequires` |
| `group` | string | Software group | `Group` |
| `description` | string | Detailed description | `%description` |
| `post_script` | string | Post-installation script | `%post` |
| `preun_script` | string | Pre-uninstallation script | `%preun` |
| `postun_script` | string | Post-uninstallation script | `%postun` |

#### Example Configuration

```json
{
  "linux": {
    "rpm": {
      "name": "myapp",
      "summary": "My application",
      "license": "MIT",
      "url": "https://example.com",
      "requires": ["python3 >= 3.8", "python3-pip"],
      "group": "Applications/Utilities",
      "description": "Detailed application description",
      "post_script": "echo 'Installation completed'\nldconfig"
    }
  }
}
```

### AppImage Configuration

UnifyPy's `platforms.linux.appimage` configuration is used to generate AppImage portable format.

#### Common Configurations

| Configuration | Type | Description |
|--------------|------|-------------|
| `desktop_entry` | boolean | Whether to generate .desktop file |
| `categories` | array | Desktop categories |
| `mime_types` | array | Supported MIME types |
| `compression` | string | Compression algorithm (gzip/xz) |
| `update_information` | string | Auto-update information |

### Official Documentation

- 📖 **Debian Policy Manual**: https://www.debian.org/doc/debian-policy/
- 📖 **Debian Control Fields**: https://www.debian.org/doc/debian-policy/ch-controlfields.html
- 📖 **RPM Packaging Guide**: https://rpm-packaging-guide.github.io/
- 📖 **RPM spec File Format**: https://rpm-software-management.github.io/rpm/manual/spec.html
- 📖 **AppImage Documentation**: https://docs.appimage.org/
- 📖 **Desktop Entry Specification**: https://specifications.freedesktop.org/desktop-entry-spec/latest/

---

## 📝 Configuration Example Files

The project provides multiple complete configuration examples for reference:

| File | Description |
|------|-------------|
| `build.json` | Basic configuration example |
| `build_multiformat.json` | Multi-format packaging configuration example |
| `build_comprehensive.json` | **Complete Feature Demonstration**, including all available configuration items |
| `build_macos_permissions_example.json` | Detailed macOS permissions configuration example |

**View Complete Configuration**:

```bash
# View complete configuration example (including all advanced options)
cat build_comprehensive.json

# Copy as your own configuration
cp build_comprehensive.json my_build.json
```
