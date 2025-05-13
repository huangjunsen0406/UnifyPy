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
      - 安装命令: `brew install create-dmg`
    - Xcode命令行工具: `xcode-select --install`
  - **Linux**: 
    - PyInstaller
    - 对应格式的打包工具:
      - DEB格式: `sudo apt-get install dpkg-dev fakeroot`
      - RPM格式: `sudo dnf install rpm-build` 或 `sudo yum install rpm-build`
      - AppImage格式: 
        ```bash
        wget -c https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
        chmod +x appimagetool-x86_64.AppImage
        sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
        ```

## 快速开始

1. **克隆仓库**

```bash
git clone https://github.com/huangjunsen0406/UnifyPy.git
cd UnifyPy
```

2. **安装依赖**

```bash
pip install -r requirements.txt
```

3. **使用方式**

有两种方式可以使用UnifyPy来打包你的项目：

**方式一：从项目目录内执行（推荐）**

进入你需要打包的项目目录，然后执行：
```bash
# 使用相对路径指向UnifyPy的main.py
python /path/to/UnifyPy/main.py . --config build.json
```

例如：
```bash
# 示例：假设UnifyPy在/home/junsen/桌面/UnifyPy目录下
python /home/junsen/桌面/UnifyPy/main.py . --config build.json
```

**方式二：从UnifyPy目录执行**

```bash
# 使用项目路径和配置文件
python main.py 你的项目路径 --config config.json
```

> **注意**：如果使用方式二，配置文件中指定的路径必须使用绝对路径。

## 使用GitHub Actions自动打包

UnifyPy支持通过GitHub Actions自动打包Windows应用程序。以下是使用步骤：

1. **复制工作流文件**

   将UnifyPy仓库中的`.github/workflows/build-windows.yml`文件复制到你的项目的`.github/workflows/`目录下。

2. **配置工作流**

   在你的GitHub仓库中，进入"Actions"标签页，选择"Build Windows Package"工作流。

3. **运行工作流**

   点击"Run workflow"按钮，在弹出的表单中：
   - `project_repo`：要打包的项目仓库（格式：用户名/仓库名），留空表示当前仓库
   - `project_path`：填写要打包的项目路径（默认为当前仓库根目录）
   - `config_file`：填写配置文件路径（默认为`build.json`）
   - `requirements_file`：项目依赖文件路径（如：requirements.txt），留空表示不安装额外依赖
   - `python_version`：选择Python版本（默认为3.10）

4. **获取打包结果**

   工作流执行完成后，可以在工作流运行记录中下载打包好的应用程序和安装程序。

> **注意**：GitHub Actions自动安装了Inno Setup，无需手动配置Inno Setup路径。

## 配置文件详解

UnifyPy使用JSON格式的配置文件进行打包配置。以下是各配置项的详细说明：

### 基本配置

```json
{
    "name": "我的应用",                  // 应用程序名称
    "display_name": "我的多平台应用",     // 应用程序显示名称
    "version": "1.0.0",                // 应用程序版本号
    "publisher": "我的公司",             // 发布者名称
    "entry": "main.py",                // 程序入口文件
    "icon": "assets/app_icon.ico",     // 应用图标路径
    "license": "LICENSE",              // 许可证文件
    "readme": "README.md",             // 自述文件
    "hooks": "hooks",                  // PyInstaller钩子目录
    "onefile": false,                  // 是否生成单文件模式的可执行文件
    "additional_pyinstaller_args": "--noconsole --add-binary assets/*.dll;.",  // 通用PyInstaller参数
    
    // 平台特定配置
    "platform_specific": {
        "windows": { ... },  // Windows平台配置
        "macos": { ... },    // macOS平台配置
        "linux": { ... }     // Linux平台配置
    }
}
```

> **注意**：JSON文件不支持注释，上述代码中的注释仅用于说明，实际配置文件中不应包含注释。

### 平台特定配置

#### Windows平台配置

```json
"windows": {
    "additional_pyinstaller_args": "--noconsole --add-data assets;assets --add-data libs;libs",
    "installer_options": {
        "languages": ["ChineseSimplified", "English"],  // 安装程序支持的语言
        "create_desktop_icon": true,                    // 是否创建桌面图标
        "allow_run_after_install": true,                // 安装后是否允许立即运行
        "license_file": "LICENSE",                      // 许可证文件
        "readme_file": "README.md",                     // 自述文件
        "require_admin": false                          // 是否需要管理员权限
    },
    "inno_setup_path": "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"  // Inno Setup路径
}
```

#### macOS平台配置

```json
"macos": {
    "additional_pyinstaller_args": "--windowed --add-data assets:assets --add-data libs:libs",
    "app_bundle_name": "我的应用.app",                   // 应用包名称
    "bundle_identifier": "com.example.myapp",          // 应用标识符
    "sign_bundle": false,                              // 是否签名应用包
    "identity": "Developer ID Application: 你的名称",    // 签名身份（如果签名）
    "entitlements": "path/to/entitlements.plist",      // 授权文件（如果需要）
    "create_dmg": true,                                // 是否创建DMG镜像
    "create_zip": false                                // 是否创建ZIP压缩包
}
```

#### Linux平台配置

```json
"linux": {
    "additional_pyinstaller_args": "--add-data assets:assets --add-data libs:libs",
    "format": "deb",                                   // 输出格式，可选值：deb, rpm, appimage
    "desktop_entry": true,                             // 是否创建桌面快捷方式
    "categories": "Utility;Development;",              // 应用程序类别
    "description": "我的Python多平台应用程序",            // 应用描述
    "requires": "libc6,libgtk-3-0,libx11-6"            // 依赖项
}
```

### 配置文件示例

完整的配置文件示例：

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

### 配置文件路径注意事项

根据使用方式不同，配置文件中的路径需要进行相应调整：

1. **从项目目录内执行（方式一）**：
   - 配置文件中的路径可以使用相对路径，相对于你的项目目录
   - 例如：`"icon": "assets/app_icon.ico"`

2. **从UnifyPy目录执行（方式二）**：
   - 配置文件中的路径必须使用绝对路径
   - 例如：`"icon": "C:/Users/username/Projects/MyApp/assets/app_icon.ico"`

**注意**：Windows系统中的路径分隔符在JSON文件中需要使用双反斜杠`\\`或单正斜杠`/`。

## 平台特定打包指南

### Windows平台打包

#### 环境准备

1. 安装PyInstaller：`pip install pyinstaller>=6.1.0`
2. 安装Inno Setup：从[官网](https://jrsoftware.org/isdl.php)下载安装
3. 配置Inno Setup路径（三种方式）：
   - 在配置文件中指定：`"inno_setup_path": "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe"`
   - 通过命令行参数：`--inno-setup-path "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"`
   - 设置环境变量：`INNO_SETUP_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe`

#### 执行打包

```bash
python /path/to/UnifyPy/main.py . --config build.json
```

#### 常见问题

1. **"无法定位程序输入点于动态链接库"错误**
   - 确保包含所有必要的DLL文件
   - 使用`--add-binary`选项添加DLL文件
   - 安装Visual C++ Redistributable包

2. **应用图标未显示**
   - 确保图标文件是有效的.ico格式
   - 使用`--icon`参数指定图标路径

3. **找不到资源文件**
   - Windows中使用分号(;)作为路径分隔符：`--add-data assets;assets`

4. **安装程序中文显示乱码**
   - 在installer_options中添加languages选项：`"languages": ["ChineseSimplified"]`
   - 确保文本文件使用UTF-8编码

### macOS平台打包

#### 环境准备

1. 安装PyInstaller：`pip install pyinstaller>=6.1.0`
2. 安装create-dmg：`brew install create-dmg`
3. 安装Xcode命令行工具：`xcode-select --install`

#### 执行打包

```bash
python /path/to/UnifyPy/main.py . --config build.json
```

#### 应用签名与公证

如果需要分发应用，建议进行签名和公证：

1. **配置签名选项**：
   ```json
   "macos": {
     "sign_bundle": true,
     "identity": "Developer ID Application: 你的名称 (Team ID)"
   }
   ```

2. **公证应用**（打包后手动执行）：
   ```bash
   xcrun altool --notarize-app --primary-bundle-id "com.example.myapp" --username "你的AppleID" --password "app-specific-password" --file "应用路径.dmg"
   ```

#### 常见问题

1. **"无法验证开发者"警告**
   - 右键点击应用，选择"打开"
   - 或执行命令：`xattr -d com.apple.quarantine /Applications/应用名称.app`

2. **应用无法找到资源文件**
   - macOS中使用冒号(:)作为路径分隔符：`--add-data assets:assets`

3. **依赖库问题（dylib无法加载）**
   - 使用`--collect-all`参数收集所有依赖：`--collect-all numpy`

### Linux平台打包

#### 环境准备

根据需要的打包格式，安装相应的工具：

1. **DEB格式**：
   ```bash
   sudo apt-get install dpkg-dev fakeroot
   ```

2. **RPM格式**：
   ```bash
   # Fedora
   sudo dnf install rpm-build
   # CentOS/RHEL
   sudo yum install rpm-build
   ```

3. **AppImage格式**：
   ```bash
   wget -c https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
   chmod +x appimagetool-x86_64.AppImage
   sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
   ```

#### 执行打包

##### DEB格式打包（适用于Debian/Ubuntu系统）

1. **准备环境**

   ```bash
   # 更新系统并安装必要的依赖
   sudo apt update
   sudo apt install -y build-essential python3-dev python3-pip python3-setuptools libopenblas-dev liblapack-dev gfortran patchelf autoconf automake libtool cmake libssl-dev libatlas-base-dev
   ```

2. **执行打包**

   确保build.json中linux.format设置为"deb"，然后执行：

   ```bash
   python3 /路径/到/UnifyPy/main.py . --config build.json
   ```

##### AppImage格式打包（适用于通用Linux系统）

AppImage格式需要特别注意NumPy库的编译，以下是完整步骤：

1. **升级pip和基本构建工具**

   ```bash
   python -m pip install --upgrade pip setuptools wheel
   ```

2. **安装必要的系统依赖**

   ```bash
   sudo apt update
   sudo apt install -y build-essential python3-dev python3-pip python3-setuptools libopenblas-dev liblapack-dev gfortran patchelf autoconf automake libtool cmake libssl-dev libatlas-base-dev
   ```

3. **安装Meson和Ninja构建系统**

   ```bash
   pip install meson ninja
   sudo apt install -y meson ninja-build
   ```

4. **准备NumPy编译环境**

   ```bash
   # 卸载现有NumPy
   pip uninstall numpy -y
   
   # 设置环境变量
   export BLAS=openblas
   export LAPACK=openblas
   export NPY_NUM_BUILD_JOBS=$(nproc)  # 使用所有CPU核心加速编译
   
   # 从源码编译安装NumPy
   pip install numpy==1.26.4 --no-binary :all:
   ```

5. **执行打包**

   确保build.json中linux.format设置为"appimage"，然后执行：

   ```bash
   python3 /路径/到/UnifyPy/main.py . --config build.json
   ```

#### 常见问题

1. **动态库依赖问题**
   - 使用`ldd`命令检查可执行文件依赖：`ldd dist/我的应用`
   - 在`requires`中添加必要的系统依赖

2. **GL/图形库问题**
   - 添加特定的图形库依赖：`"requires": "libc6,libgtk-3-0,libx11-6,libgl1-mesa-glx"`

3. **AppImage无法执行**
   - 确保添加了执行权限：`chmod +x 我的应用-1.0.0-x86_64.AppImage`
   - 检查是否安装了FUSE：`sudo apt-get install libfuse2`

4. **NumPy编译失败**
   - 确保已安装所有必要的开发库，特别是OpenBLAS、LAPACK和Fortran编译器

5. **找不到appimagetool**
   - 确保已正确安装并设置appimagetool的可执行权限

## 打包输出

成功打包后，将在项目根目录下的相应文件夹中找到打包的应用程序：

- **Windows**: 
  - 可执行文件(.exe)位于`dist/应用名称`目录
  - 安装程序位于`installer`目录，命名为`应用名称-版本号-setup.exe`

- **macOS**: 
  - 应用程序包(.app)位于`dist/应用名称`目录
  - 磁盘镜像(.dmg)位于`installer`目录，命名为`应用名称-版本号.dmg`

- **Linux**: 
  - 可执行文件位于`dist/应用名称`目录
  - 安装包位于`installer`目录：
    - DEB格式：`应用名称_版本号_amd64.deb`
    - RPM格式：`应用名称-版本号-1.x86_64.rpm`
    - AppImage格式：`应用名称-版本号-x86_64.AppImage`

## 多平台架构支持

UnifyPy会自动检测当前系统的CPU架构，并为当前架构生成对应的安装包。例如：

- 在x86_64架构的Linux上运行，会生成x86_64/amd64的安装包
- 在arm64架构的Linux上运行，会生成arm64的安装包

如果需要为同一操作系统的不同架构（如Linux的arm64和x86_64）生成安装包，需要在对应架构的机器上分别运行打包命令，或使用虚拟机/容器/交叉编译环境。

## 命令行参数说明

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
| --inno-setup-path | Inno Setup可执行文件路径 | (无) |

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

## 多平台路径分隔符注意事项

在不同平台上指定资源路径时，注意使用正确的分隔符：

- **Windows**: 使用分号 `;` (例如: `--add-data assets;assets`)
- **macOS/Linux**: 使用冒号 `:` (例如: `--add-data assets:assets`)

## 高级配置选项

### PyInstaller参数

在`additional_pyinstaller_args`字段中，您可以添加任何PyInstaller支持的参数。以下是一些常用参数：

- `--noconsole`: 不显示控制台窗口（仅适用于图形界面程序）
- `--windowed`: 等同于`--noconsole`
- `--hidden-import=MODULE`: 添加隐式导入的模块
- `--add-data SRC;DEST`: 添加数据文件（Windows平台使用分号分隔）
- `--add-data SRC:DEST`: 添加数据文件（macOS/Linux平台使用冒号分隔）
- `--icon=FILE.ico`: 设置应用程序图标

### 处理特殊依赖

某些Python库可能需要特殊处理才能正确打包，可以通过以下方式解决：

1. **使用钩子文件**：在`hooks`目录中创建自定义钩子，处理特殊导入情况
2. **添加隐式导入**：使用`--hidden-import`参数显式包含隐式导入的模块
3. **添加数据文件**：使用`--add-data`参数包含程序运行所需的数据文件

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
或者右键点击应用，选择"打开"。

**Q: 如何在同一个build.json中为Linux配置多个架构？**  
A: 当前版本不支持在同一个配置文件中为Linux指定多个架构。UnifyPy会自动检测当前系统架构并生成对应的安装包。如需为不同架构生成安装包，需要在对应架构的机器上分别运行打包命令。

## 最佳实践

1. **清理项目**：打包前移除临时文件、缓存和不必要的大型文件
2. **测试依赖**：确保所有依赖都正确安装并可以导入
3. **确认文件路径**：检查代码中的文件路径是否使用相对路径或资源路径
4. **验证配置**：确保build.json中的配置与您的环境一致
5. **多平台测试**：如果条件允许，在多个平台上测试打包的应用程序
6. **保存配置**：为不同的打包场景保存不同版本的配置文件，方便复用
7. **版本管理**：每次发布前更新版本号，保持版本一致性

## 许可证

本项目采用MIT许可证。Copyright (c) 2025 Junsen。

MIT许可证允许任何人免费使用、复制、修改、合并、发布、分发、再许可和/或销售本软件的副本，但需在所有副本中包含上述版权声明和本许可声明。

完整许可证内容请参阅[LICENSE](LICENSE)文件。

# 使用GitHub Actions打包py-xiaozhi

本指南将帮助你使用GitHub Actions和UnifyPy自动打包py-xiaozhi项目。

## 步骤1：添加工作流文件

将以下文件添加到你的py-xiaozhi仓库中：

路径: `.github/workflows/build-windows-with-unifypy.yml`

```yaml
name: Build Windows Package with UnifyPy

on:
  workflow_dispatch:
    inputs:
      python_version:
        description: 'Python版本'
        required: false
        default: '3.10'
        type: choice
        options:
          - '3.9'
          - '3.10'
          - '3.11'
          - '3.12'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - name: Checkout py-xiaozhi
        uses: actions/checkout@v4
        
      - name: Checkout UnifyPy
        uses: actions/checkout@v4
        with:
          repository: huangjunsen0406/UnifyPy
          path: UnifyPy
          
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ github.event.inputs.python_version }}
          
      - name: Install PyInstaller
        run: |
          python -m pip install --upgrade pip
          pip install pyinstaller>=6.1.0
          
      - name: Install py-xiaozhi dependencies
        run: |
          pip install -r requirements.txt
          
      - name: Install Inno Setup
        shell: powershell
        run: |
          # 下载Inno Setup安装程序
          Invoke-WebRequest -Uri "https://files.jrsoftware.org/is/6/innosetup-6.2.1.exe" -OutFile "innosetup-6.2.1.exe"
          
          # 使用静默安装模式安装Inno Setup
          Start-Process -FilePath "innosetup-6.2.1.exe" -ArgumentList "/VERYSILENT", "/SUPPRESSMSGBOXES" -Wait
          
          # 设置环境变量
          echo "INNO_SETUP_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
          
      - name: Run UnifyPy
        shell: cmd
        run: |
          python UnifyPy\main.py . --config build.json
          
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: xiaozhi-windows-package
          path: |
            dist/**/*.exe
            installer/**/*.exe
```

## 步骤2：运行工作流

1. 在GitHub上进入你的py-xiaozhi仓库
2. 点击"Actions"选项卡
3. 选择左侧的"Build Windows Package with UnifyPy"工作流
4. 点击"Run workflow"按钮
5. 在弹出的表单中填写：
   - `target_repo`：要打包的目标仓库（格式：用户名/仓库名），留空表示当前仓库
   - `python_version`：选择Python版本（默认为3.10）
6. 点击绿色的"Run workflow"按钮开始构建

## 步骤3：下载打包结果

1. 等待工作流完成（通常需要5-10分钟）
2. 在工作流运行记录中点击"xiaozhi-windows-package"构件
3. 下载构件压缩包，其中包含：
   - `dist/xiaozhi/xiaozhi.exe`：可执行文件
   - `installer/xiaozhi-1.0.0-setup.exe`：安装程序

## 注意事项

- 确保你的py-xiaozhi仓库中有正确的`build.json`文件
- 工作流会自动处理依赖项和Inno Setup的安装
- 如果遇到问题，可以查看工作流运行日志进行排查

## 自定义打包

如果需要自定义打包过程，可以修改：

1. `build.json`文件中的配置选项
2. `.github/workflows/build-windows-with-unifypy.yml`工作流文件

## 相关链接

- [UnifyPy项目](https://github.com/huangjunsen0406/UnifyPy)
- [py-xiaozhi项目](https://github.com/huangjunsen0406/py-xiaozhi)