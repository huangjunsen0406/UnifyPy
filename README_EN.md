# UnifyPy 2.0

> Professional Cross-Platform Python Application Packaging Solution

## 🚀 Project Overview

UnifyPy 2.0 is an enterprise-grade cross-platform Python application packaging tool that supports packaging Python projects into native installers for Windows, macOS, and Linux platforms.

### ✨ Core Features

- **🔄 Multi-Platform Support**: Windows (EXE+MSI), macOS (DMG+PKG+ZIP), Linux (DEB+RPM+AppImage+TarGZ)
- **⚡ Parallel Building**: Support multi-format parallel generation, significantly improving build efficiency
- **🛡️ Enterprise Features**: Automatic rollback, session management, intelligent error handling
- **🎨 Excellent Experience**: Rich progress bars, staged display, detailed logging
- **🔧 Complete Configuration**: Support 30+ PyInstaller parameters, JSON configuration
- **📦 Automated Tools**: Automatic download and management of third-party tools

## 📦 Installation Requirements

### System Requirements
- Python 3.8+
- Windows 10+ / macOS 10.14+ / Linux (Ubuntu 18.04+)

### Dependency Installation
```bash
pip install -r requirements.txt
```

Main dependencies:
- pyinstaller >= 6.0
- rich >= 12.0
- requests >= 2.28
- packaging >= 21.0

## 🚀 Quick Start

### Basic Usage

```bash
# Package using configuration file
python main.py . --config build.json

# Quick packaging via command line
python main.py . --name myapp --version 1.0.0 --entry main.py --onefile

# Multi-format parallel build
python main.py . --config build_multiformat.json --parallel --max-workers 4

# Verbose output mode
python main.py . --config build.json --verbose

# Clean rebuild
python main.py . --config build.json --clean --verbose

# Generate executable only, skip installer
python main.py . --config build.json --skip-installer

# Specify specific format
python main.py . --config build.json --format dmg --parallel

# macOS development mode (automatic permission configuration)
python main.py . --config py-xiaozhi.json --development --verbose
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
  "icon": "assets/app_icon.png",
  
  "pyinstaller": {
    "onefile": false,
    "windowed": true,
    "clean": true,
    "noconfirm": true,
    "add_data": ["assets:assets"],
    "hidden_import": ["requests", "json"]
  },
  
  "platforms": {
    "windows": {
      "inno_setup": {
        "create_desktop_icon": true,
        "languages": ["english", "chinesesimplified"]
      }
    },
    "macos": {
      "bundle_identifier": "com.mycompany.myapp",
      "dmg": {
        "volname": "MyApp Installer",
        "window_size": [600, 400]
      }
    },
    "linux": {
      "deb": {
        "package": "myapp",
        "depends": ["python3 (>= 3.8)"]
      }
    }
  }
}
```

## 🔧 Command Line Arguments

### Basic Syntax
```bash
python main.py <project_dir> [options]
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

## 📋 Supported Packaging Formats

### Windows
- **EXE** (Inno Setup) - Standard installer
- **MSI** - Windows Installer package

### macOS  
- **DMG** - Disk image installer
- **PKG** - macOS native installer
- **ZIP** - Portable archive

### Linux
- **DEB** - Debian/Ubuntu package
- **RPM** - Red Hat/CentOS package
- **AppImage** - Portable application image
- **TAR.GZ** - Source archive

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

## 🔄 Parallel Building

UnifyPy 2.0 supports multi-format parallel building to significantly improve build efficiency:

```bash
# Enable parallel building
python main.py . --config build_multiformat.json --parallel

# Specify number of worker threads
python main.py . --parallel --max-workers 4

# View parallel building effects
python main.py . --config build_comprehensive.json --parallel --verbose
```

## 🛡️ Rollback System

Automatically track build operations with one-click rollback support:

```bash
# List available rollback sessions
python main.py . --list-rollback

# Execute rollback
python main.py . --rollback SESSION_ID

# Disable automatic rollback
python main.py . --config build.json --no-rollback
```

## 📁 Project Structure

```
UnifyPy/
├── main.py                 # Main entry file
├── requirements.txt        # Python dependencies
├── build.json             # Standard configuration example
├── build_multiformat.json # Multi-format configuration
├── build_comprehensive.json # Complete configuration example
├── py-xiaozhi.json        # Real project configuration example
└── src/                   # Source code
    ├── core/             # Core modules (configuration management)
    ├── platforms/        # Platform packagers
    ├── pyinstaller/      # PyInstaller integration
    ├── tools/            # Built-in tools (create-dmg, etc.)
    └── utils/            # Utility modules
```

## 🔍 Troubleshooting

### Common Issues

**Q: PyInstaller packaging failed?**
```bash
# Check dependencies
pip install pyinstaller>=5.0

# Clean and retry
python main.py . --config build.json --clean --verbose
```

**Q: macOS permission configuration issues?**
- Check permission descriptions in configuration file
- Ensure Bundle ID format is correct
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
python main.py . --parallel --max-workers 2

# Or disable parallel building
python main.py . --config build.json
```

### Debugging Tips

1. **Enable verbose output**: `--verbose`
2. **Check logs**: View detailed build process information
3. **Step-by-step build**: Use `--skip-exe` or `--skip-installer`
4. **Rollback testing**: Use `--list-rollback` to view history

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
- Let tools automatically convert icon formats
- Test dependency compatibility across different platforms

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🤝 Contributing

Issues and Pull Requests are welcome!

---

UnifyPy 2.0 - Making Python Application Packaging Simple and Efficient 🚀