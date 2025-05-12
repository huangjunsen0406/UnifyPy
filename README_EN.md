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
      - Download: https://jrsoftware.org/isdl.php
      - After installation, specify ISCC.exe path via --inno-setup-path parameter
      - Or set the INNO_SETUP_PATH environment variable
  - **macOS**: 
    - PyInstaller
    - create-dmg (for creating DMG images)
      - Install command: `brew install create-dmg`
    - Xcode Command Line Tools: `xcode-select --install`
  - **Linux**: 
    - PyInstaller
    - Format-specific packaging tools:
      - DEB format: `sudo apt-get install dpkg-dev fakeroot`
      - RPM format: `sudo dnf install rpm-build` or `sudo yum install rpm-build`
      - AppImage format:
        ```bash
        wget -c https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
        chmod +x appimagetool-x86_64.AppImage
        sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
        ```

## Quick Start

1. **Clone the repository**

```bash
git clone https://github.com/huangjunsen0406/UnifyPy.git
cd UnifyPy
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

## Configuration File Guide

UnifyPy uses JSON format configuration files for packaging. Here's a detailed explanation of the configuration options:

### Basic Configuration

```json
{
    "name": "MyApp",                    // Application name
    "display_name": "My Multi-Platform App",  // Display name
    "version": "1.0.0",                 // Version number
    "publisher": "My Company",          // Publisher name
    "entry": "main.py",                 // Entry Python file
    "icon": "assets/app_icon.ico",      // Application icon path
    "license": "LICENSE",               // License file
    "readme": "README.md",              // README file
    "hooks": "hooks",                   // PyInstaller hooks directory
    "onefile": false,                   // Whether to generate single-file executable
    "additional_pyinstaller_args": "--noconsole --add-binary assets/*.dll;.",  // Common PyInstaller arguments
    
    // Platform-specific configurations
    "platform_specific": {
        "windows": { ... },  // Windows platform configuration
        "macos": { ... },    // macOS platform configuration
        "linux": { ... }     // Linux platform configuration
    }
}
```

> **Note**: JSON files don't support comments. The comments above are for explanation only and should not be included in actual configuration files.

### Platform-Specific Configurations

#### Windows Platform Configuration

```json
"windows": {
    "additional_pyinstaller_args": "--noconsole --add-data assets;assets --add-data libs;libs",
    "installer_options": {
        "languages": ["English", "ChineseSimplified"],  // Supported languages
        "create_desktop_icon": true,                    // Create desktop icon
        "allow_run_after_install": true,                // Allow running after installation
        "license_file": "LICENSE",                      // License file
        "readme_file": "README.md",                     // README file
        "require_admin": false                          // Require admin privileges
    },
    "inno_setup_path": "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"  // Inno Setup path
}
```

#### macOS Platform Configuration

```json
"macos": {
    "additional_pyinstaller_args": "--windowed --add-data assets:assets --add-data libs:libs",
    "app_bundle_name": "MyApp.app",                    // App bundle name
    "bundle_identifier": "com.example.myapp",          // Bundle identifier
    "sign_bundle": false,                              // Sign the app bundle
    "identity": "Developer ID Application: Your Name", // Signing identity (if signing)
    "entitlements": "path/to/entitlements.plist",      // Entitlements file (if needed)
    "create_dmg": true,                                // Create DMG image
    "create_zip": false                                // Create ZIP archive
}
```

#### Linux Platform Configuration

```json
"linux": {
    "additional_pyinstaller_args": "--add-data assets:assets --add-data libs:libs",
    "format": "deb",                                   // Output format: deb, rpm, or appimage
    "desktop_entry": true,                             // Create desktop shortcut
    "categories": "Utility;Development;",              // Application categories
    "description": "My Python Multi-Platform Application",  // Application description
    "requires": "libc6,libgtk-3-0,libx11-6"            // Dependencies
}
```

### Configuration File Example

Complete configuration file example:

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

## Platform-Specific Packaging Guides

### Windows Platform Packaging

#### Environment Setup

1. Install PyInstaller: `pip install pyinstaller>=6.1.0`
2. Install Inno Setup: Download from [official website](https://jrsoftware.org/isdl.php)
3. Configure Inno Setup path (three methods):
   - Specify in configuration file: `"inno_setup_path": "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"`
   - Via command line parameter: `--inno-setup-path "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"`
   - Set environment variable: `INNO_SETUP_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe`

#### Execute Packaging

```bash
python /path/to/UnifyPy/main.py . --config build.json
```

#### Common Issues

1. **"Unable to locate program entry point in DLL" error**
   - Ensure all necessary DLL files are included
   - Use the `--add-binary` option to add DLL files
   - Install Visual C++ Redistributable package

2. **Application icon not showing**
   - Ensure the icon file is a valid .ico format
   - Use the `--icon` parameter to specify the icon path

3. **Resource files not found**
   - Windows uses semicolon (;) as path separator: `--add-data assets;assets`

4. **Installer shows garbled text for non-English languages**
   - Add languages option in installer_options: `"languages": ["ChineseSimplified"]`
   - Ensure text files use UTF-8 encoding

### macOS Platform Packaging

#### Environment Setup

1. Install PyInstaller: `pip install pyinstaller>=6.1.0`
2. Install create-dmg: `brew install create-dmg`
3. Install Xcode Command Line Tools: `xcode-select --install`

#### Execute Packaging

```bash
python /path/to/UnifyPy/main.py . --config build.json
```

#### App Signing and Notarization

If you need to distribute your application, it's recommended to sign and notarize it:

1. **Configure signing options**:
   ```json
   "macos": {
     "sign_bundle": true,
     "identity": "Developer ID Application: Your Name (Team ID)"
   }
   ```

2. **Notarize the application** (manually execute after packaging):
   ```bash
   xcrun altool --notarize-app --primary-bundle-id "com.example.myapp" --username "your_apple_id" --password "app-specific-password" --file "app_path.dmg"
   ```

#### Common Issues

1. **"Cannot verify developer" warning**
   - Right-click the application and select "Open"
   - Or run the command: `xattr -d com.apple.quarantine /Applications/AppName.app`

2. **Application cannot find resource files**
   - macOS uses colon (:) as path separator: `--add-data assets:assets`

3. **Library dependency issues (dylib cannot load)**
   - Use the `--collect-all` parameter to collect all dependencies: `--collect-all numpy`

### Linux Platform Packaging

#### Environment Setup

Install the appropriate tools based on your desired packaging format:

1. **DEB format**:
   ```bash
   sudo apt-get install dpkg-dev fakeroot
   ```

2. **RPM format**:
   ```bash
   # Fedora
   sudo dnf install rpm-build
   # CentOS/RHEL
   sudo yum install rpm-build
   ```

3. **AppImage format**:
   ```bash
   wget -c https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
   chmod +x appimagetool-x86_64.AppImage
   sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
   ```

#### Execute Packaging

##### DEB Package Format (for Debian/Ubuntu systems)

1. **Prepare the environment**

   ```bash
   # Update system and install necessary dependencies
   sudo apt update
   sudo apt install -y build-essential python3-dev python3-pip python3-setuptools libopenblas-dev liblapack-dev gfortran patchelf autoconf automake libtool cmake libssl-dev libatlas-base-dev
   ```

2. **Execute packaging**

   Ensure that linux.format is set to "deb" in your build.json, then run:

   ```bash
   python3 /path/to/UnifyPy/main.py . --config build.json
   ```

##### AppImage Format (for universal Linux distribution)

AppImage format requires special attention to NumPy library compilation. Here are the complete steps:

1. **Upgrade pip and basic build tools**

   ```bash
   python -m pip install --upgrade pip setuptools wheel
   ```

2. **Install necessary system dependencies**

   ```bash
   sudo apt update
   sudo apt install -y build-essential python3-dev python3-pip python3-setuptools libopenblas-dev liblapack-dev gfortran patchelf autoconf automake libtool cmake libssl-dev libatlas-base-dev
   ```

3. **Install Meson and Ninja build systems**

   ```bash
   pip install meson ninja
   sudo apt install -y meson ninja-build
   ```

4. **Prepare NumPy compilation environment**

   ```bash
   # Uninstall existing NumPy
   pip uninstall numpy -y
   
   # Set environment variables
   export BLAS=openblas
   export LAPACK=openblas
   export NPY_NUM_BUILD_JOBS=$(nproc)  # Use all CPU cores to speed up compilation
   
   # Compile and install NumPy from source
   pip install numpy==1.26.4 --no-binary :all:
   ```

5. **Execute packaging**

   Ensure that linux.format is set to "appimage" in your build.json, then run:

   ```bash
   python3 /path/to/UnifyPy/main.py . --config build.json
   ```

#### Common Issues

1. **Dynamic library dependency issues**
   - Use the `ldd` command to check executable dependencies: `ldd dist/myapp`
   - Add necessary system dependencies in the `requires` field

2. **GL/Graphics library issues**
   - Add specific graphics library dependencies: `"requires": "libc6,libgtk-3-0,libx11-6,libgl1-mesa-glx"`

3. **AppImage cannot execute**
   - Ensure execution permissions are set: `chmod +x MyApp-1.0.0-x86_64.AppImage`
   - Check if FUSE is installed: `sudo apt-get install libfuse2`

4. **NumPy compilation failure**
   - Ensure all necessary development libraries are installed, especially OpenBLAS, LAPACK, and Fortran compiler

5. **Cannot find appimagetool**
   - Ensure appimagetool is correctly installed and has proper execution permissions

## Packaging Output

After successful packaging, you'll find the packaged application in the respective folders in your project root directory:

- **Windows**: 
  - Executable file (.exe) in the `dist/app_name` directory
  - Installer in the `installer` directory, named `app_name-version-setup.exe`

- **macOS**: 
  - Application bundle (.app) in the `dist/app_name` directory
  - Disk image (.dmg) in the `installer` directory, named `app_name-version.dmg`

- **Linux**: 
  - Executable file in the `dist/app_name` directory
  - Installation package in the `installer` directory:
    - DEB format: `app_name_version_amd64.deb`
    - RPM format: `app_name-version-1.x86_64.rpm`
    - AppImage format: `app_name-version-x86_64.AppImage`

## Multi-Platform Architecture Support

UnifyPy automatically detects the current system's CPU architecture and generates installation packages accordingly. For example:

- When running on Linux x86_64, it generates x86_64/amd64 packages
- When running on Linux arm64, it generates arm64 packages

If you need to generate packages for different architectures of the same operating system (e.g., Linux arm64 and x86_64), you need to run the packaging command on separate machines with the corresponding architectures, or use virtual machines/containers/cross-compilation environments.

## Command Line Parameters

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
| --inno-setup-path | Inno Setup executable path | (None) |

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

## Path Separator Notes for Different Platforms

When specifying resource paths on different platforms, use the correct separator:

- **Windows**: Use semicolon `;` (e.g., `--add-data assets;assets`)
- **macOS/Linux**: Use colon `:` (e.g., `--add-data assets:assets`)

## Advanced Configuration Options

### PyInstaller Parameters

In the `additional_pyinstaller_args` field, you can add any parameters supported by PyInstaller. Here are some commonly used parameters:

- `--noconsole`: Hide the console window (only for GUI applications)
- `--windowed`: Same as `--noconsole`
- `--hidden-import=MODULE`: Add implicitly imported modules
- `--add-data SRC;DEST`: Add data files (Windows platform uses semicolon)
- `--add-data SRC:DEST`: Add data files (macOS/Linux platform uses colon)
- `--icon=FILE.ico`: Set application icon

### Handling Special Dependencies

Some Python libraries may require special handling to package correctly. This can be resolved through:

1. **Using hook files**: Create custom hooks in the `hooks` directory to handle special import cases
2. **Adding implicit imports**: Use the `--hidden-import` parameter to explicitly include implicitly imported modules
3. **Adding data files**: Use the `--add-data` parameter to include data files needed by the program

## Common Issues

**Q: Windows platform shows "Inno Setup not found" when building installer**  
A: You need to manually install Inno Setup:
1. Visit https://jrsoftware.org/isdl.php to download the latest version
2. After installation, specify the ISCC.exe path using one of these methods:
   - Via --inno-setup-path parameter: `python main.py project_path --inno-setup-path "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"`
   - In config.json: `"inno_setup_path": "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"`
   - Set the INNO_SETUP_PATH environment variable

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
Or right-click the application and select "Open".

**Q: How to configure multiple architectures for Linux in a single build.json?**  
A: The current version doesn't support specifying multiple architectures in a single configuration file. UnifyPy automatically detects the current system architecture and generates the corresponding package. To generate packages for different architectures, you need to run the packaging command on separate machines with the corresponding architectures.

## Best Practices

1. **Clean your project**: Remove temporary files, caches, and unnecessary large files before packaging
2. **Test dependencies**: Ensure all dependencies are correctly installed and can be imported
3. **Verify file paths**: Check if file paths in your code use relative paths or resource paths
4. **Validate configuration**: Ensure the configuration in build.json matches your environment
5. **Test on multiple platforms**: If possible, test the packaged application on multiple platforms
6. **Save configurations**: Save different versions of configuration files for different packaging scenarios for easy reuse
7. **Version management**: Update version numbers before each release to maintain version consistency

## License

This project is licensed under the MIT License. Copyright (c) 2025 Junsen.

The MIT License allows anyone to freely use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, provided that the above copyright notice and permission notice are included in all copies.

See the [LICENSE](LICENSE) file for the complete license text.
