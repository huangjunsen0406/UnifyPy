# UnifyPy 2.0

> Professional Cross-Platform Python Application Packaging Solution

## 🚀 Project Overview

UnifyPy 2.0 is an enterprise-grade cross-platform Python application packaging tool that supports packaging Python projects into native installers for Windows, macOS, and Linux platforms.

### ✨ Core Features

- **🔄 Multi-Platform Support (64-bit)**: Windows (EXE), macOS (DMG), Linux (DEB+RPM)
- **⚡ Parallel Building**: Support multi-format parallel generation, significantly improving build efficiency
- **🛡️ Enterprise Features**: Automatic rollback, session management, intelligent error handling
- **🎨 Excellent Experience**: Rich progress bars, staged display, detailed logging
- **🔧 Complete Configuration**: Support 30+ PyInstaller parameters, JSON configuration
- **📦 Automated Tools**: Automatic download and management of third-party tools
- **🍎 macOS Permission Management**: Auto-generate permission files, code signing support
- **📊 Smart Path Handling**: Automatic resolution of relative paths to absolute paths
- **🧩 Plugin Architecture**: Event-driven plugin system with engine and event bus, support external plugin extensions

## 📦 Installation

### System Requirements

- Python 3.8+
- Windows 10+ / macOS 10.14+ / Linux (Ubuntu 18.04+)

### Install UnifyPy

```bash
pip install unifypy
```

### Platform-Specific Tools

- **Windows**: Inno Setup (auto-detected)
- **macOS**: create-dmg (bundled), Xcode Command Line Tools
- **Linux**: dpkg-dev, rpm-build, fakeroot (auto-install guidance as needed)

## 🚀 Quick Start

### Option 1: Interactive Wizard (Recommended for Beginners)

Use the interactive wizard to quickly generate configuration files:

```bash
# Launch interactive configuration wizard
unifypy . --init

# Or specify project directory
unifypy /path/to/project --init
```

The wizard will guide you through:
1. Basic information (name, version, entry file, etc.)
2. Target platform selection (macOS/Windows/Linux)
3. PyInstaller packaging configuration
4. Platform-specific configuration (permissions, icons, install options, etc.)
5. Generate `build.json` configuration file
6. Optionally start building immediately

> 💡 **Tip**: After the wizard completes, it generates a standard `build.json` file that you can manually edit to add advanced configurations. See [Interactive Wizard Guide](#-interactive-wizard-guide) for details.

### Option 2: Command Line Quick Packaging

```bash
# Package using configuration file
unifypy . --config build.json

# Quick packaging via command line
unifypy . --name myapp --version 1.0.0 --entry main.py --onefile

# Multi-format parallel build
unifypy . --config build_multiformat.json --parallel --max-workers 4

# Verbose output mode
unifypy . --config build.json --verbose

# Clean rebuild
unifypy . --config build.json --clean --verbose

# Generate executable only, skip installer
unifypy . --config build.json --skip-installer

# Specify specific format
unifypy . --config build.json --format dmg --parallel

# macOS development mode (automatic permission configuration)
unifypy . --config build.json --development --verbose

# Dry run (env check + prepare only)
unifypy . --config build.json --dry-run
```

## 🧩 Plugin System & External Plugins

- Lifecycle events:
  `on_start → handle_rollback_commands → load_config → environment_check → prepare → build_executable → generate_installers → on_success → on_exit`
- Extend by subscribing to events with your plugin class.
- External plugins (top-level in build.json):
```json
{
  "plugins": [
    "my_package.my_plugin:MyPlugin"
  ]
}
```

### Configuration File Example

Create `build.json` configuration file:

```json
{
  "name": "MyApp",
  "display_name": "My Application", 
  "version": "1.0.0",
  "publisher": "My Company",
  "entry": "main.py",
  "icon": "assets/icon.png",
  
  "pyinstaller": {
    "onefile": false,
    "windowed": true,
    "clean": true,
    "noconfirm": true,
    "add_data": ["assets:assets", "config:config"],
    "hidden_import": ["requests", "json", "tkinter"]
  },
  
  "platforms": {
    "windows": {
      "pyinstaller": {
        "add_data": ["assets;assets", "config;config"]
      },
      "inno_setup": {
        "create_desktop_icon": true,
        "create_start_menu_icon": true,
        "languages": ["english", "chinesesimplified"],
        "license_file": "LICENSE",
        "setup_icon": "assets/installer.ico"
      }
    },
    "macos": {
      "bundle_identifier": "com.mycompany.myapp",
      "microphone_usage_description": "Microphone access required for voice features",
      "camera_usage_description": "Camera access required for video features",
      "dmg": {
        "volname": "MyApp Installer",
        "window_size": [600, 400],
        "icon_size": 100
      }
    },
    "linux": {
      "deb": {
        "package": "myapp",
        "depends": ["python3 (>= 3.8)", "libgtk-3-0"],
        "description": "My Python Application"
      },
      "rpm": {
        "summary": "My Python Application",
        "license": "MIT",
        "url": "https://example.com/myapp"
      }
    }
  },

  "plugins": [
    "my_package.my_plugin:MyPlugin"
  ]
}
```

## 🔧 Command Line Arguments

### Basic Syntax
```bash
unifypy <project_dir> [options]
```

### Basic Information Parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `project_dir` | Python project root directory path (required) | `. or /path/to/project` |
| `--config CONFIG` | Configuration file path (JSON format) | `--config build.json` |
| `--name NAME` | Application name | `--name MyApp` |
| `--display-name DISPLAY_NAME` | Application display name | `--display-name "My Application"` |
| `--entry ENTRY` | Entry Python file | `--entry main.py` |
| `--version VERSION` | Application version | `--version 1.0.0` |
| `--publisher PUBLISHER` | Publisher name | `--publisher "My Company"` |

### File and Resource Parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `--icon ICON` | Icon file path | `--icon assets/app.png` |
| `--license LICENSE` | License file path | `--license LICENSE.txt` |
| `--readme README` | README file path | `--readme README.md` |
| `--hooks HOOKS` | Runtime hooks directory | `--hooks hooks/` |

### PyInstaller Options
| Parameter | Description | Example |
|-----------|-------------|---------|
| `--onefile` | Generate single-file executable | `--onefile` |
| `--windowed` | Windowed mode (no console) | `--windowed` |
| `--console` | Console mode | `--console` |

### Build Control Options
| Parameter | Description | Example |
|-----------|-------------|---------|
| `--skip-exe` | Skip executable build | `--skip-exe` |
| `--skip-installer` | Skip installer build | `--skip-installer` |
| `--clean` | Clean previous build files | `--clean` |
| `--format FORMAT` | Specify output format | `--format dmg` |

### Tool Path Options
| Parameter | Description | Example |
|-----------|-------------|---------|
| `--inno-setup-path INNO_SETUP_PATH` | Inno Setup executable path | `--inno-setup-path /path/to/ISCC.exe` |

### Output Control Options
| Parameter | Description | Example |
|-----------|-------------|---------|
| `--verbose, -v` | Show verbose output | `--verbose` or `-v` |
| `--quiet, -q` | Silent mode | `--quiet` or `-q` |

### Performance Optimization Options
| Parameter | Description | Example |
|-----------|-------------|---------|
| `--parallel` | Enable parallel building | `--parallel` |
| `--max-workers MAX_WORKERS` | Maximum parallel worker threads | `--max-workers 4` |

### Rollback System Options
| Parameter | Description | Example |
|-----------|-------------|---------|
| `--no-rollback` | Disable automatic rollback | `--no-rollback` |
| `--rollback SESSION_ID` | Execute rollback for specified session | `--rollback abc123` |
| `--list-rollback` | List available rollback sessions | `--list-rollback` |

### macOS Development Options
| Parameter | Description | Example |
|-----------|-------------|---------|
| `--development` | Force development version (enable debug permissions) | `--development` |
| `--production` | Production version (disable debug permissions, for signed apps only) | `--production` |

### Help Options
| Parameter | Description | Example |
|-----------|-------------|---------|
| `-h, --help` | Show help information and exit | `--help` |

## 🧙 Interactive Wizard Guide

The interactive wizard provides a friendly interface that guides you through configuration file creation via Q&A.

### Launch Wizard

```bash
# Launch in current project directory
unifypy . --init

# Specify project directory
unifypy /path/to/project --init
```

### Interaction Flow

#### 1️⃣ Basic Configuration

| Configuration | Description | Default | Purpose |
|--------------|-------------|---------|---------|
| **Entry file** | Python entry file | `main.py` | Specifies the main program entry point, PyInstaller analyzes dependencies from this file |
| **Project name** | Project name | Inferred from entry file | Used for executable file name, automatically converted to legal file name format |
| **Display name** | Display name | Same as project name | Name displayed in installer and application menu, supports Chinese and spaces |
| **Version** | Version number | `1.0.0` | Application version, recommended to use semantic versioning (e.g. 1.0.0, 2.1.3) |
| **Publisher** | Publisher | Optional | Publisher or company name, used for installer and application info |
| **Description** | Application description | Optional | Brief application description, used for package managers and installers |
| **Icon path** | Icon path | `assets/icon.png` | Application icon, supports PNG/ICO/ICNS formats, UnifyPy auto-converts |

**Operation**:
- Enter text and press `Enter` to confirm
- Press `Enter` directly to use default value
- Enter `?` to view detailed help

#### 2️⃣ Target Platform Selection

| Platform | Supported Formats | Description |
|----------|------------------|-------------|
| **macOS** | DMG disk image | Standard macOS installer format, drag-and-drop installation |
| **Windows** | EXE installer | Standard Windows installer based on Inno Setup |
| **Linux** | DEB, RPM, AppImage | DEB (Debian/Ubuntu), RPM (RedHat/CentOS), AppImage (universal portable) |

**Operation**:
- Use `↑` `↓` arrow keys to move cursor
- Press `Space` to select/deselect
- Press `Enter` to confirm selection
- Current platform is selected by default

#### 3️⃣ PyInstaller Configuration

| Configuration | Options | Description | Recommended Scenarios |
|--------------|---------|-------------|----------------------|
| **Single file mode** | Yes / No | `onefile: true/false` | **Yes**: Single executable file, easy to distribute but slower startup<br>**No**: Directory mode, includes dependencies, fast startup but more files |
| **Windowed mode** | Yes / No | `windowed: true/false` | **Yes**: Window application, hides console window (GUI apps)<br>**No**: Console application, shows command-line window (CLI tools) |
| **Data directories** | Multi-select | Resource directories to package | Auto-scans project directories, recommends common directories (assets, models, src, etc.)<br>Selected directories will be packaged into the application |

**Operation**:
- **Single file mode / Windowed mode**: Use `←` `→` left/right arrow keys to switch, `Enter` to confirm
- **Data directories**: Use `↑` `↓` up/down keys to move, `Space` to select, `Enter` to confirm

**Data Directory Notes**:
- ✅ Auto-recommended: `assets`, `resources`, `data`, `models`, `src`, `config`, etc.
- 🚫 Auto-excluded: `__pycache__`, `.git`, `venv`, `build`, `dist`, etc.
- 📊 Display info: File count and directory size

#### 4️⃣ macOS Platform Configuration (if macOS selected)

| Configuration | Description | Example | Purpose |
|--------------|-------------|---------|---------|
| **Bundle Identifier** | macOS app unique identifier | `com.company.appname` | Used to identify the application, format: reverse domain + app name |
| **Minimum macOS version** | Minimum supported system version | `10.13` | Specifies the minimum macOS version the app supports |
| **App category** | Application category | Productivity | Category in App Store and Launchpad |
| **Permissions** | System permissions selection | Multi-select | Select system permissions the app needs (microphone, camera, etc.) |
| **Copyright** | Copyright notice | `© 2024 Company` | Copyright text displayed in application info |

**Available Permissions List**:

| Permission | Use Case | Corresponding Info.plist Key |
|-----------|----------|------------------------------|
| Microphone (麦克风) | Recording, speech recognition | `NSMicrophoneUsageDescription` |
| Camera (摄像头) | Photography, video calls | `NSCameraUsageDescription` |
| Speech Recognition (语音识别) | Speech-to-text | `NSSpeechRecognitionUsageDescription` |
| Local Network (本地网络) | LAN access | `NSLocalNetworkUsageDescription` |
| Audio (音频) | Audio playback | `NSAppleMusicUsageDescription` |
| Accessibility (辅助功能) | Global shortcuts, automation | `NSAccessibilityUsageDescription` |
| Documents Folder (文档文件夹) | Read/write documents | `NSDocumentsFolderUsageDescription` |
| Downloads Folder (下载文件夹) | Manage downloads | `NSDownloadsFolderUsageDescription` |
| Apple Events (自动化) | AppleScript, inter-app communication | `NSAppleEventsUsageDescription` |
| Calendar (日历) | Read/write calendar events | `NSCalendarsUsageDescription` |
| Contacts (通讯录) | Read/write contacts | `NSContactsUsageDescription` |
| Location (位置) | Get geographic location | `NSLocationUsageDescription` |
| Photos (照片) | Access photo library | `NSPhotoLibraryUsageDescription` |

**Operation**:
- Use `↑` `↓` arrow keys to move
- Press `Space` to select/deselect
- Press `Enter` to confirm selection

> 💡 **Tip**: Permission descriptions use generic text, you can customize description text in the generated `build.json`.

#### 5️⃣ Windows Platform Configuration (if Windows selected)

| Configuration | Options | Description |
|--------------|---------|-------------|
| **Desktop icon** | Yes / No | Whether to create desktop shortcut |
| **Start menu shortcut** | Yes / No | Whether to create start menu shortcut |
| **Allow run after install** | Yes / No | Whether to ask user to run app immediately after installation |
| **Languages** | Multi-select | Installer supported languages (Chinese, English, Japanese, etc.) |

**Available Languages**:
- Simplified Chinese (chinesesimplified)
- Traditional Chinese (chinesetraditional)
- English (english)
- Japanese (japanese)
- Korean (korean)
- French (french)
- German (german)
- Spanish (spanish)

**Operation**:
- **Icons and shortcuts**: Use `←` `→` arrow keys, `Enter` to confirm
- **Languages**: Use `↑` `↓` up/down keys, `Space` to select, `Enter` to confirm

#### 6️⃣ Linux Platform Configuration (if Linux selected)

| Configuration | Options | Description |
|--------------|---------|-------------|
| **Package formats** | DEB / RPM / AppImage | Select package formats to generate (multi-select) |
| **Package name** | Text | Package name (lowercase letters, numbers, hyphens) |
| **Desktop categories** | Multi-select | Application categories in desktop environment |

**Package Format Description**:
- **DEB**: Used by Debian, Ubuntu, Linux Mint, etc.
- **RPM**: Used by RedHat, CentOS, Fedora, etc.
- **AppImage**: Universal portable format, no installation required, double-click to run

**Desktop Categories**:
- AudioVideo (audio/video)
- Development (development)
- Education (education)
- Game (games)
- Graphics (graphics)
- Network (network)
- Office (office)
- Utility (utility)
- System (system)

#### 7️⃣ Configuration Summary and Save

The wizard displays a complete configuration summary, including:
- 📋 Project info (name, version, publisher, etc.)
- 📦 Packaging configuration (mode, console, data directories)
- 🌍 Target platforms and detailed configurations for each platform

After confirmation:
1. Save as `build.json` file
2. Show advanced configuration options (can be manually edited)
3. Ask whether to start building immediately

**Immediate Build Option**:
- **Yes**: Execute `unifypy . --config build.json --clean` to start packaging
- **No**: Only save configuration, manually run later

### After Wizard Completion

After the wizard completes, it displays a prompt explaining how to manually edit `build.json` to add advanced configurations:

```
💡 You can manually edit build.json to add advanced configurations:

  📘 PyInstaller Advanced Options:
     • hidden_import: Dynamically imported modules
     • exclude_module: Exclude unnecessary modules to reduce size
     • runtime_hook: Runtime hook scripts
     • splash: Splash screen
     → Reference: https://pyinstaller.org/en/stable/usage.html

  🪟 Windows Advanced Options:
     • compression: Compression algorithm
     • license_file: License file
     → Reference: https://jrsoftware.org/ishelp/

  🍎 macOS Advanced Options:
     • target_architecture: Architecture selection
     • codesign_identity: Code signing certificate
     → Reference: https://developer.apple.com/documentation/

  🐧 Linux Advanced Options:
     • depends: Dependency package list
     • postinst_script: Post-installation script
     → See documentation in "Advanced Configuration Reference" section below

  📚 Complete Configuration Examples:
     • View build_comprehensive.json
```

## 📋 Supported Packaging Formats

### Windows
- **EXE** (Inno Setup) - Standard installer

### macOS
- **DMG** - Disk image installer

### Linux
- **DEB** - Debian/Ubuntu package
- **RPM** - Red Hat/CentOS package

## ⚙️ Configuration File Details

### Global Configuration
```json
{
  "name": "Application Name",
  "display_name": "Display Name", 
  "version": "Version Number",
  "publisher": "Publisher",
  "entry": "Entry File",
  "icon": "Icon File",
  "license": "License File",
  "readme": "README File"
}
```

### PyInstaller Configuration
```json
{
  "pyinstaller": {
    "onefile": false,
    "windowed": true,
    "clean": true,
    "noconfirm": true,
    "optimize": 2,
    "strip": true,
    "add_data": ["source_path:target_path"],
    "hidden_import": ["module_name"],
    "exclude_module": ["excluded_module"]
  }
}
```

### macOS Specific Configuration
```json
{
  "platforms": {
    "macos": {
      "bundle_identifier": "com.company.app",
      "minimum_system_version": "10.14.0",
      "category": "public.app-category.productivity",

      "microphone_usage_description": "Microphone access required for voice features",
      "camera_usage_description": "Camera access required for video features",

      "dmg": {
        "volname": "Installer Name",
        "window_size": [600, 400],
        "icon_size": 100
      }
    }
  }
}
```

## 📚 Advanced Configuration Reference

UnifyPy supports all native configuration items of underlying tools. Configuration items are directly mapped to corresponding tool parameters, so you can refer to official documentation of each tool to use advanced features.

For detailed advanced configuration options, see:

📖 **[Advanced Configuration Documentation](docs/advanced-configuration-en.md)**

Including:
- **PyInstaller Advanced Configuration**: hidden_import, exclude_module, runtime_hook, splash and 30+ configuration items
- **Windows Advanced Configuration**: Inno Setup script configuration, compression algorithms, installer wizard styles, etc.
- **macOS Advanced Configuration**: Info.plist configuration, DMG customization, code signing, architecture selection, etc.
- **Linux Advanced Configuration**: DEB/RPM package configuration, dependency management, installation scripts, etc.

### 📝 Configuration Example Files

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

## 🔄 Parallel Building

UnifyPy 2.0 supports multi-format parallel building to significantly improve build efficiency:

```bash
# Enable parallel building
unifypy . --config build_multiformat.json --parallel

# Specify number of worker threads
unifypy . --parallel --max-workers 4

# View parallel building effects
unifypy . --config build_comprehensive.json --parallel --verbose
```

## 🛡️ Rollback System

Automatically track build operations with one-click rollback support:

```bash
# List available rollback sessions
unifypy . --list-rollback

# Execute rollback
unifypy . --rollback SESSION_ID

# Disable automatic rollback
unifypy . --config build.json --no-rollback
```

## 🍎 macOS Special Features

### Automatic Permission Management
UnifyPy 2.0 provides a complete permission management solution for macOS applications:

```bash
# Development mode - auto-generate permission files, suitable for development and testing
unifypy . --config build.json --development

# Production mode - for signed applications
unifypy . --config build.json --production
```

### Permission Configuration Example
```json
{
  "platforms": {
    "macos": {
      "bundle_identifier": "com.company.myapp",
      "microphone_usage_description": "Microphone access required for voice features",
      "camera_usage_description": "Camera access required for video features", 
      "location_usage_description": "Location access required for location-based services"
    }
  }
}
```

### Automated Features
- ✅ Auto-generate entitlements.plist
- ✅ Auto-update Info.plist permission descriptions  
- ✅ Auto ad-hoc code signing
- ✅ Auto icon format conversion (PNG → ICNS)

## 🔄 Smart Path Handling

UnifyPy 2.0 solves path issues when packaging across directories:

### Problem Scenario
```bash
# Packaging other projects from UnifyPy directory
cd /path/to/UnifyPy
unifypy ../my-project --config ../my-project/build.json
```

### Smart Solution
Relative paths in configuration files are automatically resolved relative to the **target project directory**:
- ✅ `"icon": "assets/icon.png"` → `/path/to/my-project/assets/icon.png`  
- ✅ `"add_data": ["data:data"]` → `/path/to/my-project/data:data`
- ✅ Support nested configurations and platform-specific paths

### Supported Path Fields
- Single files: `icon`, `license`, `readme`, `entry`, `setup_icon`, `version_file`
- Array fields: `add_data`, `add_binary`, `datas`, `binaries`
- Formats: Support both `source:dest` and `source;dest` separators

## 🏗️ Architecture Design

UnifyPy 2.0 adopts an event-driven plugin-based architecture:

### Core Architecture Components

**Engine + EventBus**

UnifyPy 2.0's core uses an engine-driven plugin architecture that coordinates plugin lifecycle through an event bus:

```python
# Build lifecycle events
ON_START → HANDLE_ROLLBACK_COMMANDS → LOAD_CONFIG →
ENVIRONMENT_CHECK → PREPARE → BUILD_EXECUTABLE →
GENERATE_INSTALLERS → ON_SUCCESS → ON_EXIT
```

**Plugin System**

All features are implemented as plugins, supporting priority control and external plugin extensions:

```python
class MyPlugin(BasePlugin):
    name = "my_plugin"
    priority = 50  # Lower number = higher priority

    def register(self, bus: EventBus):
        bus.subscribe(ON_START, self.on_start, priority=self.priority)
        bus.subscribe(BUILD_EXECUTABLE, self.on_build, priority=self.priority)
```

**External Plugin Support**

Declare external plugins in configuration file:

```json
{
  "plugins": [
    "my_package.my_plugin:MyPlugin",
    "company.custom_plugin:CustomPlugin"
  ]
}
```

### Core Design Patterns

**Registry Pattern**
```python
# Dynamically register and lookup packagers
packager_registry = PackagerRegistry()
packager_class = packager_registry.get_packager("macos", "dmg")
```

**Strategy Pattern**
```python
# Each packager implements specific format packaging strategy
class DMGPackager(BasePackager):
    def package(self, format_type, source_path, output_path):
        # DMG-specific packaging logic
```

**Event-Driven Pattern**
```python
# Plugins respond to different build phases by subscribing to events
bus.subscribe(PREPARE, self.prepare_build, priority=10)
bus.subscribe(BUILD_EXECUTABLE, self.build, priority=50)
```

### Core Component Interactions

```mermaid
graph TD
    A[Engine] --> B[EventBus]
    A --> C[BuildContext]

    B --> D[ProgressPlugin]
    B --> E[ConfigPlugin]
    B --> F[PyInstallerPlugin]
    B --> G[PackagingPlugin]
    B --> H[RollbackPlugin]
    B --> I[External Plugins...]

    E --> J[ConfigManager]
    J --> K[Path Resolution]

    G --> L[PackagerRegistry]
    L --> M[WindowsPackager]
    L --> N[MacOSPackager]
    L --> O[LinuxPackager]

    H --> P[RollbackManager]
```

### Build Process

1. **Initialization Phase (ON_START)**
   - Initialize progress manager
   - Create build context
   - Load external plugins

2. **Config Loading Phase (LOAD_CONFIG)**
   - Parse command line arguments
   - Load and merge configuration files
   - Smart path resolution (relative→absolute)

3. **Environment Check Phase (ENVIRONMENT_CHECK)**
   - Validate project structure and dependencies
   - Check tool availability
   - Platform compatibility check

4. **Preparation Phase (PREPARE)**
   - Create build directories and temporary files
   - Initialize rollback system
   - macOS permission file auto-generation

5. **Executable Building (BUILD_EXECUTABLE)**
   - PyInstaller configuration building
   - Automatic icon format conversion
   - macOS Info.plist update and code signing

6. **Installer Generation (GENERATE_INSTALLERS)**
   - Select appropriate packager based on platform
   - Support parallel building of multiple formats
   - Auto-validate output files

7. **Success Completion (ON_SUCCESS)**
   - Display build results summary
   - Output file manifest

8. **Exit Cleanup (ON_EXIT)**
   - Clean temporary files
   - Save rollback data
   - Close progress manager

## 📁 Project Structure

```
UnifyPy/
├── pyproject.toml      # Project configuration and dependencies
├── build.json         # Standard configuration example
└── unifypy/          # Source code package
    ├── __main__.py   # CLI entry point
    ├── cli/          # Command-line interface
    ├── core/         # Core modules (engine, event_bus, plugin, config...)
    ├── plugins/      # Built-in plugins (progress, config, pyinstaller, packaging...)
    ├── platforms/    # Platform packagers (windows, macos, linux)
    ├── pyinstaller/  # PyInstaller integration
    ├── templates/    # Template files
    ├── tools/        # Built-in tools
    └── utils/        # Utility modules
```

## 🔍 Troubleshooting

### Common Issues

**Q: PyInstaller packaging failed?**
```bash
# Check dependencies
pip install pyinstaller>=5.0

# Clean and retry
unifypy . --config build.json --clean --verbose
```

**Q: macOS permission configuration issues?**
```bash
# Use development mode to auto-generate permission files
unifypy . --config build.json --development --verbose

# Check generated permission files
cat auto_generated_entitlements.plist
```
- Check permission descriptions in configuration file
- Ensure Bundle ID format is correct (com.company.appname)
- Refer to `build_macos_permissions_example.json`

**Q: Linux dependencies missing?**
```bash
# Ubuntu/Debian
sudo apt-get install dpkg-dev fakeroot

# CentOS/RHEL
sudo yum install rpm-build
```

**Q: Parallel build failed?**
```bash
# Reduce number of worker threads
unifypy . --parallel --max-workers 2

# Or disable parallel building
unifypy . --config build.json
```

**Q: Configuration file paths not found?**
```bash
# Ensure relative paths are relative to project directory
# ✅ Correct: Project at /path/to/myapp, icon at /path/to/myapp/assets/icon.png
"icon": "assets/icon.png"

# ❌ Wrong: Using paths relative to UnifyPy directory
"icon": "../myapp/assets/icon.png"

# Check path resolution
unifypy . --config build.json --verbose
```

### Debugging Tips

1. **Enable verbose output**: `--verbose`
2. **Check logs**: View detailed build process information
3. **Step-by-step build**: Use `--skip-exe` or `--skip-installer`
4. **Rollback testing**: Use `--list-rollback` to view history
5. **Path issues**: Check if relative paths in config file are correct
6. **Permission issues**: Use `--development` mode on macOS for debugging

## 📝 Best Practices

### Configuration File Management
- Use different configuration files for different environments (development, testing, production)
- Include configuration file templates in version control
- Use environment variables for sensitive information

### Build Optimization
- Enable parallel building to improve efficiency
- Configure `exclude_module` appropriately to reduce package size
- Use `clean` to ensure clean build environment

### Cross-Platform Compatibility
- Use `/` for path separators or let tools handle automatically
- Let tools automatically convert icon formats (PNG→ICNS/ICO)
- Test dependency compatibility across different platforms
- **Important**: Relative paths in config files are automatically resolved to absolute paths relative to project directory

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🤝 Contributing

Issues and Pull Requests are welcome!

---

UnifyPy 2.0 - Making Python Application Packaging Simple and Efficient 🚀
