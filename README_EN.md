# UnifyPy

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.6+](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/downloads/)

UnifyPy is a powerful automated solution that can package any Python project into standalone executables and installers across platforms. It supports Windows, macOS, and Linux, providing a unified interface and rich configuration options.

## Features

- **Cross-platform support**: Compatible with Windows, macOS, and Linux
- **Multiple installer formats**:
  - Windows: Executable (.exe) and installer (Inno Setup)
  - macOS: Application bundle (.app) and disk image (.dmg)
  - Linux: AppImage, DEB, RPM packages
- **Flexible configuration**: Supports both command-line arguments and JSON configuration files
- **Packaging modes**: Supports both single-file and directory modes
- **Customization options**: Supports custom icons, version numbers, publisher info, and more
- **Resource bundling**: Automatically handles resource files, dependencies, and custom hooks
- **Automatic dependency installation**: Detects and installs required tools

## Requirements

- Python 3.6 or higher
- Platform-specific requirements:
  - **Windows**: 
    - PyInstaller
    - Inno Setup (for creating installers)
  - **macOS**: 
    - PyInstaller
    - create-dmg (for creating DMG images)
  - **Linux**: 
    - PyInstaller
    - Format-specific packaging tools (dpkg-deb, rpmbuild, appimagetool)

## Quick Start

1. **Clone the repository**

```bash
git clone https://github.com/huangjunsen0406/UnifyPy.git
cd python-packager
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Usage Methods**

There are two ways to use UnifyPy to package your project:

**Method 1: Execute from within your project directory (Recommended)**

Navigate to your project directory that needs to be packaged, then run:
```bash
# Use the relative path to UnifyPy's main.py
python /path/to/UnifyPy/main.py . --config build.json
```

For example:
```bash
# Example: If UnifyPy is located at /home/junsen/Desktop/UnifyPy
python /home/junsen/Desktop/UnifyPy/main.py . --config build.json
```

**Method 2: Execute from UnifyPy directory**

```bash
# Using project path and configuration file
python main.py your_project_path --config config.json
```

> **Note**: If using Method 2, the paths specified in the configuration file must use absolute paths.

## Usage Examples

### Command Line Examples

#### Windows Platform

```bash
# Basic usage
python main.py C:\Projects\MyApp --name "MyApp" --entry app.py

# Advanced usage
python main.py C:\Projects\MyApp --name "MyApp" --entry app.py --version "1.2.3" --publisher "My Company" --icon "assets/icon.ico" --hooks hooks_dir
```

#### macOS Platform

```bash
# Basic usage
python3 main.py /Users/username/Projects/MyApp --name "MyApp" --entry app.py

# Generate DMG image
python3 main.py /Users/username/Projects/MyApp --config macos_config.json
```

#### Linux Platform

```bash
# Generate AppImage format
python3 main.py /home/username/Projects/MyApp --config linux_appimage.json

# Generate DEB package
python3 main.py /home/username/Projects/MyApp --config linux_deb.json
```

### Configuration File Example

Create a JSON configuration file with packaging parameters:

```json
{
  "name": "MyApp",
  "display_name": "My Multi-Platform App",
  "version": "1.0.0",
  "publisher": "My Company",
  "entry": "main.py",
  "icon": "assets/app_icon.ico",
  "license": "LICENSE",
  "readme": "README.md",
  "hooks": "hooks",
  "onefile": false,
  "additional_pyinstaller_args": "--noconsole --add-binary assets/*.dll;.",
  
  "platform_specific": {
    "windows": {
      "additional_pyinstaller_args": "--noconsole --add-data assets;assets --add-data libs;libs",
      "installer_options": {
        "languages": ["English", "ChineseSimplified"],
        "create_desktop_icon": true,
        "allow_run_after_install": true
      }
    },
    "macos": {
      "additional_pyinstaller_args": "--windowed --add-data assets:assets --add-data libs:libs",
      "app_bundle_name": "MyApp.app",
      "bundle_identifier": "com.example.myapp",
      "sign_bundle": false,
      "create_dmg": true
    },
    "linux": {
      "additional_pyinstaller_args": "--add-data assets:assets --add-data libs:libs",
      "format": "deb",
      "desktop_entry": true,
      "categories": "Utility;Development;",
      "description": "My Python Multi-Platform Application",
      "requires": "libc6,libgtk-3-0,libx11-6"
    }
  }
}
```

### Configuration File Path Notes

Depending on how you use UnifyPy, the paths in your configuration file need to be adjusted accordingly:

1. **When executing from your project directory (Method 1)**:
   - Paths in the configuration file can use relative paths, relative to your project directory
   - Example: `"icon": "assets/app_icon.ico"`

2. **When executing from UnifyPy directory (Method 2)**:
   - Paths in the configuration file must use absolute paths
   - Example: `"icon": "C:/Users/username/Projects/MyApp/assets/app_icon.ico"`

**Note**: Path separators in Windows systems must use double backslashes `\\` or single forward slashes `/` in JSON files.

## Installing Packaged Applications

### Windows

- Run the `.exe` installer
- Follow the installation wizard
- The program will be installed in the default directory with Start menu and desktop shortcuts

### macOS

- Mount the `.dmg` file
- Drag the application to the Applications folder
- Launch the app from Launchpad

### Linux

**DEB packages (Debian/Ubuntu)**:
```bash
sudo apt install ./appname_version_architecture.deb
```

**RPM packages (Fedora/CentOS)**:
```bash
sudo rpm -i appname-version.architecture.rpm
```

**AppImage**:
```bash
chmod +x AppName-version-architecture.AppImage
./AppName-version-architecture.AppImage
```

## Parameters

| Parameter | Description | Default Value |
|-----------|-------------|---------------|
| project_dir | Python project root directory path | (Required) |
| --name | Application name | Project directory name |
| --display-name | Application display name | Same as name |
| --entry | Entry Python file | main.py |
| --version | Application version | 1.0 |
| --publisher | Publisher name | Python Application Team |
| --icon | Icon file path | (Auto-generated) |
| --license | License file path | (None) |
| --readme | README file path | (None) |
| --config | Configuration file path (JSON format) | (None) |
| --hooks | Runtime hooks directory | (None) |
| --skip-exe | Skip executable packaging step | (No) |
| --skip-installer | Skip installer generation step | (No) |
| --onefile | Generate single-file executable | (No) |

## Path Separator Notes for Different Platforms

When specifying resource paths on different platforms, use the correct separator:

- **Windows**: Use semicolon `;` (e.g., `--add-data assets;assets`)
- **macOS/Linux**: Use colon `:` (e.g., `--add-data assets:assets`)

## Common Issues

**Q: Linux application shows missing dependencies after packaging**  
A: Add required dependencies in the Linux configuration:
```json
"linux": {
  "requires": "libc6,libgtk-3-0,libx11-6,libopenblas-dev"
}
```

**Q: How to resolve MKL-related errors?**  
A: Add OpenBLAS as an alternative dependency, or ensure NumPy and other libraries use open-source BLAS backends before packaging.

**Q: macOS app won't start, showing "unidentified developer" warning**  
A: Try enabling code signing in the configuration:
```json
"macos": {
  "sign_bundle": true,
  "identity": "Your Developer ID"
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
