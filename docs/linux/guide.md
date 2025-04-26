# Linux应用打包指南

本文档提供在Linux平台上打包Python应用程序的详细指南，包括打包过程、注意事项以及常见问题的解决方案。

## 目录

- [环境准备](#环境准备)
- [基本打包流程](#基本打包流程)
- [支持的打包格式](#支持的打包格式)
- [配置选项](#配置选项)
- [配置示例](#配置示例)
- [常见问题](#常见问题)

## 环境准备

在Linux上打包Python应用，需要准备以下环境：

1. **Python环境**：
   - 建议使用Python 3.7+
   - 使用虚拟环境隔离项目依赖：`python -m venv venv`

2. **PyInstaller**：
   ```bash
   pip install pyinstaller>=6.1.0
   ```

3. **打包工具**（根据目标格式选择）：
   - **AppImage**：
     ```bash
     # 获取AppImageKit工具
     wget -c https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
     chmod +x appimagetool-x86_64.AppImage
     sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
     ```
   
   - **DEB包**：
     ```bash
     sudo apt-get install dpkg-dev fakeroot
     ```
   
   - **RPM包**：
     ```bash
     # Fedora
     sudo dnf install rpm-build
     # CentOS/RHEL
     sudo yum install rpm-build
     ```

4. **其他依赖**：
   - 如需创建桌面集成，安装相应工具：
     ```bash
     sudo apt-get install desktop-file-utils # Debian/Ubuntu
     sudo dnf install desktop-file-utils # Fedora
     ```

## 基本打包流程

### 1. 使用配置文件

创建`build.json`配置文件：

```json
{
  "name": "我的应用",
  "display_name": "我的应用",
  "version": "1.0.0",
  "entry": "main.py",
  "icon": "assets/icon.png",
  "platform_specific": {
    "linux": {
      "additional_pyinstaller_args": "--add-data assets:assets --add-data models:models",
      "format": "appimage",
      "desktop_entry": true,
      "categories": "Utility;Development",
      "description": "我的Python应用程序"
    }
  }
}
```

### 2. 执行打包命令

```bash
python3 main.py 项目路径 --config build.json
```

### 3. 输出文件

成功打包后，将在以下位置生成文件：

- 可执行文件：`项目路径/dist/我的应用` 或 `项目路径/dist/我的应用/我的应用`（取决于是单文件模式还是目录模式）
- 安装包（根据选择的格式）：
  - AppImage: `项目路径/installer/我的应用-1.0.0-x86_64.AppImage`
  - DEB: `项目路径/installer/我的应用_1.0.0_amd64.deb`
  - RPM: `项目路径/installer/我的应用-1.0.0-1.x86_64.rpm`

## 支持的打包格式

### AppImage

AppImage是一种通用的Linux应用打包格式，具有以下特点：
- 无需安装，直接运行
- 跨发行版兼容
- 自包含，包含所有依赖
- 便于分发和使用

### DEB包

DEB是Debian/Ubuntu系列发行版的标准软件包格式：
- 集成软件包管理
- 支持依赖管理
- 安装/卸载方便
- 适合Debian、Ubuntu、Mint等发行版

### RPM包

RPM是Red Hat系列发行版的标准软件包格式：
- 集成软件包管理
- 支持依赖管理
- 安装/卸载方便
- 适合Fedora、CentOS、RHEL等发行版

## 配置选项

### PyInstaller选项

以下是Linux平台下常用的PyInstaller配置选项：

| 选项 | 说明 | 示例 |
|------|------|------|
| --onefile | 创建单文件可执行程序 | `--onefile` |
| --add-data | 添加资源文件 | `--add-data "assets:assets"` |
| --add-binary | 添加二进制文件 | `--add-binary "libs:."` |
| --hidden-import | 添加隐式导入 | `--hidden-import numpy` |
| --collect-all | 收集整个包 | `--collect-all PIL` |

### Linux特有选项

UnifyPy支持以下Linux特有配置选项：

| 选项 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| format | 打包格式 | appimage | `"appimage"`, `"deb"`, `"rpm"` |
| desktop_entry | 创建桌面条目 | false | `true` |
| categories | 应用类别 | Utility | `"Utility;Development"` |
| description | 应用描述 | | `"我的Python应用"` |
| requires | 软件包依赖 | | `"libc6,libgtk-3-0"` |

## 配置示例

### AppImage配置

```json
{
  "name": "我的应用",
  "display_name": "我的应用",
  "version": "1.0.0",
  "entry": "main.py",
  "icon": "assets/icon.png",
  "platform_specific": {
    "linux": {
      "additional_pyinstaller_args": "--add-data assets:assets",
      "format": "appimage",
      "desktop_entry": true,
      "categories": "Utility;Development",
      "description": "我的Python应用程序"
    }
  }
}
```

### DEB包配置

```json
{
  "name": "我的应用",
  "display_name": "我的应用",
  "version": "1.0.0",
  "publisher": "开发者",
  "entry": "main.py",
  "icon": "assets/icon.png",
  "platform_specific": {
    "linux": {
      "additional_pyinstaller_args": "--add-data assets:assets",
      "format": "deb",
      "desktop_entry": true,
      "categories": "Utility;Development",
      "description": "我的Python应用程序",
      "requires": "libc6,libgtk-3-0,libx11-6"
    }
  }
}
```

### RPM包配置

```json
{
  "name": "我的应用",
  "display_name": "我的应用",
  "version": "1.0.0",
  "publisher": "开发者",
  "entry": "main.py",
  "icon": "assets/icon.png",
  "platform_specific": {
    "linux": {
      "additional_pyinstaller_args": "--add-data assets:assets",
      "format": "rpm",
      "desktop_entry": true,
      "categories": "Utility;Development",
      "description": "我的Python应用程序",
      "requires": "gtk3,libX11"
    }
  }
}
```

## 常见问题

### 1. 动态库依赖问题

**症状**：应用启动时报错找不到某些.so文件
**解决方案**：
- 使用`ldd`命令检查可执行文件依赖：`ldd dist/我的应用`
- 在`additional_pyinstaller_args`中添加`--collect-all`选项
- 对于DEB/RPM包，在`requires`中添加必要的系统依赖

### 2. GL/图形库问题

**症状**：使用OpenGL或图形库的应用崩溃
**解决方案**：
- 确保包含所有必要的库文件
- 添加特定的图形库依赖：
  ```json
  "requires": "libc6,libgtk-3-0,libx11-6,libgl1-mesa-glx"
  ```
- 使用`--collect-all`选项包含整个图形库

### 3. AppImage无法执行

**症状**：创建的AppImage无法执行
**解决方案**：
- 确保添加了执行权限：`chmod +x 我的应用-1.0.0-x86_64.AppImage`
- 检查是否安装了FUSE：`sudo apt-get install libfuse2`
- 使用--no-fuse选项运行：`./我的应用-1.0.0-x86_64.AppImage --no-fuse`

### 4. 字体和图标问题

**症状**：应用中的字体显示不正确或图标丢失
**解决方案**：
- 将必要的字体和图标文件包含在应用中
- 使用以下配置确保打包字体：
  ```
  --add-data "/usr/share/fonts/truetype/some-font:/usr/share/fonts/truetype/some-font"
  ```

### 5. 缺少glibc版本

**症状**：在较旧的Linux发行版上无法运行，报GLIBC版本错误
**解决方案**：
- 在较旧的Linux发行版上构建应用
- 使用容器或虚拟机在特定目标环境中构建
- 尝试使用静态链接（部分依赖）：在PyInstaller命令中添加`--exclude-module _bootlocale` 