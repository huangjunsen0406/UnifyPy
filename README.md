# UnifyPy

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.6+](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/downloads/)

UnifyPy是一个强大的自动化解决方案，能将任何Python项目打包成跨平台的独立可执行文件和安装程序。支持Windows、macOS和Linux三大主流操作系统，提供统一的接口和丰富的配置选项。

## 功能特点

- **跨平台支持**：适配Windows、macOS和Linux三大主流平台
- **多种安装包格式**：
  - Windows: 可执行文件(.exe)和安装程序(Inno Setup)
  - macOS: 应用程序包(.app)和磁盘镜像(.dmg)
  - Linux: AppImage, DEB, RPM格式安装包
- **灵活配置**：支持命令行参数和JSON配置文件两种配置方式
- **打包模式**：支持单文件模式和目录模式
- **自定义选项**：支持自定义图标、版本号、发布者等元数据
- **资源打包**：自动处理资源文件、依赖库、自定义钩子等
- **自动安装依赖**：自动检测并安装所需工具

## 安装要求

- Python 3.6或更高版本
- 各平台特定要求：
  - **Windows**: 
    - PyInstaller
    - Inno Setup (用于创建安装程序)
      - 下载地址: https://jrsoftware.org/isdl.php
      - 安装后，可通过--inno-setup-path参数指定ISCC.exe路径
      - 或设置INNO_SETUP_PATH环境变量
  - **macOS**: 
    - PyInstaller
    - create-dmg (用于创建DMG镜像)
  - **Linux**: 
    - PyInstaller
    - 对应格式的打包工具(dpkg-deb, rpmbuild, appimagetool)

## 快速开始

1. **克隆仓库**

```bash
git clone https://github.com/huangjunsen0406/UnifyPy.git
cd python-packager
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **基本使用**

```bash
# 使用默认配置打包项目
python main.py 你的项目路径

# 使用JSON配置文件打包
python main.py 你的项目路径 --config config.json
```

## 使用示例

### 命令行参数示例

#### Windows平台

```bash
# 基本用法
python main.py C:\Projects\MyApp --name "我的应用" --entry app.py

# 高级用法
python main.py C:\Projects\MyApp --name "我的应用" --entry app.py --version "1.2.3" --publisher "我的公司" --icon "assets/icon.ico" --hooks hooks目录
```

#### macOS平台

```bash
# 基本用法
python3 main.py /Users/username/Projects/MyApp --name "我的应用" --entry app.py

# 生成DMG镜像
python3 main.py /Users/username/Projects/MyApp --config macos_config.json
```

#### Linux平台

```bash
# 生成AppImage格式
python3 main.py /home/username/Projects/MyApp --config linux_appimage.json

# 生成DEB包
python3 main.py /home/username/Projects/MyApp --config linux_deb.json
```

### 配置文件示例

创建一个包含打包参数的JSON配置文件：

```json
{
  "name": "我的应用",
  "display_name": "我的多平台应用",
  "version": "1.0.0",
  "publisher": "我的公司",
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
        "languages": ["ChineseSimplified", "English"],
        "create_desktop_icon": true,
        "allow_run_after_install": true
      }
    },
    "macos": {
      "additional_pyinstaller_args": "--windowed --add-data assets:assets --add-data libs:libs",
      "app_bundle_name": "我的应用.app",
      "bundle_identifier": "com.example.myapp",
      "sign_bundle": false,
      "create_dmg": true
    },
    "linux": {
      "additional_pyinstaller_args": "--add-data assets:assets --add-data libs:libs",
      "format": "deb",
      "desktop_entry": true,
      "categories": "Utility;Development;",
      "description": "我的Python多平台应用程序",
      "requires": "libc6,libgtk-3-0,libx11-6"
    }
  }
}
```

## 安装打包后的应用

### Windows

- 直接运行`.exe`安装程序
- 按照安装向导完成安装
- 程序将安装在默认目录，并创建开始菜单和桌面快捷方式

### macOS

- 挂载`.dmg`文件
- 将应用拖到Applications文件夹
- 在Launchpad中启动应用

### Linux

**DEB包 (Debian/Ubuntu)**:
```bash
sudo apt install ./应用名称_版本_架构.deb
```

**RPM包 (Fedora/CentOS)**:
```bash
sudo rpm -i 应用名称-版本.架构.rpm
```

**AppImage**:
```bash
chmod +x 应用名称-版本-架构.AppImage
./应用名称-版本-架构.AppImage
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| project_dir | Python项目根目录路径 | (必填) |
| --name | 应用程序名称 | 项目目录名称 |
| --display-name | 应用程序显示名称 | 与name相同 |
| --entry | 入口Python文件 | main.py |
| --version | 应用程序版本 | 1.0 |
| --publisher | 发布者名称 | Python应用开发团队 |
| --icon | 图标文件路径 | (自动生成) |
| --license | 许可证文件路径 | (无) |
| --readme | 自述文件路径 | (无) |
| --config | 配置文件路径(JSON格式) | (无) |
| --hooks | 运行时钩子目录 | (无) |
| --skip-exe | 跳过exe打包步骤 | (否) |
| --skip-installer | 跳过安装程序生成步骤 | (否) |
| --onefile | 生成单文件模式的可执行文件 | (否) |

## 多平台路径分隔符注意事项

在不同平台上指定资源路径时，注意使用正确的分隔符：

- **Windows**: 使用分号 `;` (例如: `--add-data assets;assets`)
- **macOS/Linux**: 使用冒号 `:` (例如: `--add-data assets:assets`)

## 常见问题

**Q: Windows平台构建安装程序时提示找不到Inno Setup**  
A: 需要手动安装Inno Setup:
1. 访问 https://jrsoftware.org/isdl.php 下载最新版
2. 安装后，有以下方式指定ISCC.exe路径:
   - 通过--inno-setup-path参数: `python main.py 项目路径 --inno-setup-path "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"`
   - 在config.json中配置: `"inno_setup_path": "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"`
   - 设置环境变量INNO_SETUP_PATH

**Q: 打包后的Linux应用提示缺少依赖库**  
A: 在Linux配置中添加所需依赖：
```json
"linux": {
  "requires": "libc6,libgtk-3-0,libx11-6,libopenblas-dev"
}
```

**Q: 如何解决MKL相关错误?**  
A: 添加OpenBLAS作为替代依赖，或在打包前确保NumPy等库使用开源BLAS后端。

**Q: macOS应用无法启动，提示"未识别的开发者"**  
A: 可以尝试在配置中启用代码签名：
```json
"macos": {
  "sign_bundle": true,
  "identity": "你的开发者ID"
}
```

## 许可证

本项目采用MIT许可证。Copyright (c) 2025 Junsen。

MIT许可证允许任何人免费使用、复制、修改、合并、发布、分发、再许可和/或销售本软件的副本，但需在所有副本中包含上述版权声明和本许可声明。

完整许可证内容请参阅[LICENSE](LICENSE)文件。