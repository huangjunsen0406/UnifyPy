# Windows应用打包指南

本文档提供在Windows平台上打包Python应用程序的详细指南，包括打包过程、注意事项以及常见问题的解决方案。

## 目录

- [环境准备](#环境准备)
- [基本打包流程](#基本打包流程)
- [Inno Setup安装](#inno-setup安装)
- [配置选项](#配置选项)
- [配置示例](#配置示例)
- [常见问题](#常见问题)

## 环境准备

在Windows上打包Python应用，需要准备以下环境：

1. **Python环境**：
   - 建议使用Python 3.7+
   - 使用虚拟环境隔离项目依赖：`python -m venv venv`

2. **PyInstaller**：
   ```cmd
   pip install pyinstaller>=6.1.0
   ```

3. **Inno Setup**（用于创建安装程序）：
   - 下载并安装 [Inno Setup](https://jrsoftware.org/isdl.php)
   - 将Inno Setup的安装路径添加到环境变量PATH中

4. **其他依赖**：
   - 建议安装Visual C++ 运行时，以确保打包的应用可以在其他系统上运行
   - 如需处理特殊资源文件，可能需要额外的工具

## 基本打包流程

### 1. 使用配置文件

创建`build.json`配置文件：

```json
{
  "name": "我的应用",
  "display_name": "我的应用",
  "version": "1.0.0",
  "publisher": "开发者名称",
  "entry": "main.py",
  "icon": "assets/icon.ico",
  "platform_specific": {
    "windows": {
      "additional_pyinstaller_args": "--noconsole --add-data assets;assets --add-data data;data",
      "installer_options": {
        "languages": ["ChineseSimplified", "English"],
        "create_desktop_icon": true,
        "allow_run_after_install": true
      }
    }
  }
}
```

### 2. 执行打包命令

```cmd
python main.py 项目路径 --config build.json
```

### 3. 输出文件

成功打包后，将在以下位置生成文件：

- 可执行文件：`项目路径/dist/我的应用.exe` 或 `项目路径/dist/我的应用/我的应用.exe`（取决于是单文件模式还是目录模式）
- 安装程序：`项目路径/installer/我的应用-1.0.0-setup.exe`

## Inno Setup安装

Inno Setup是一个免费的安装程序制作工具，可以创建专业的Windows安装程序。

### 安装步骤

1. 访问 [Inno Setup官网](https://jrsoftware.org/isdl.php) 下载最新版本
2. 运行安装程序，按照向导完成安装
3. 安装时建议将Inno Setup添加到PATH环境变量中

### 配置路径

有三种方式设置Inno Setup路径：

1. **环境变量**：
   - 创建名为`INNO_SETUP_PATH`的环境变量，值为Inno Setup安装目录
   - 例如：`C:\Program Files (x86)\Inno Setup 6`

2. **命令行参数**：
   ```cmd
   python main.py 项目路径 --inno-setup-path "C:\Program Files (x86)\Inno Setup 6"
   ```

3. **配置文件**：
   ```json
   {
     "platform_specific": {
       "windows": {
         "inno_setup_path": "C:\\Program Files (x86)\\Inno Setup 6"
       }
     }
   }
   ```

## 配置选项

### PyInstaller选项

以下是Windows平台下常用的PyInstaller配置选项：

| 选项 | 说明 | 示例 |
|------|------|------|
| --noconsole | 创建无控制台窗口的应用 | `--noconsole` |
| --onefile | 创建单文件可执行程序 | `--onefile` |
| --add-data | 添加资源文件 | `--add-data "assets;assets"` |
| --add-binary | 添加二进制文件 | `--add-binary "libs/dll;."` |
| --icon | 指定应用图标 | `--icon "assets/icon.ico"` |
| --version-file | 指定版本信息文件 | `--version-file "version.txt"` |
| --uac-admin | 要求管理员权限运行 | `--uac-admin` |

### Inno Setup选项

UnifyPy支持以下Inno Setup配置选项：

| 选项 | 说明 | 示例 |
|------|------|------|
| languages | 支持的语言 | `["ChineseSimplified", "English"]` |
| create_desktop_icon | 创建桌面图标 | `true` |
| allow_run_after_install | 安装后允许运行 | `true` |
| license_file | 许可证文件 | `"LICENSE"` |
| readme_file | 自述文件 | `"README.txt"` |
| require_admin | 要求管理员权限安装 | `false` |
| custom_inno_script | 自定义Inno脚本 | `"installer/custom.iss"` |

## 配置示例

### 基本配置（目录模式）

```json
{
  "name": "我的应用",
  "display_name": "我的应用",
  "version": "1.0.0",
  "publisher": "开发者名称",
  "entry": "main.py",
  "icon": "assets/icon.ico",
  "platform_specific": {
    "windows": {
      "additional_pyinstaller_args": "--noconsole --add-data assets;assets"
    }
  }
}
```

### 高级配置（单文件模式）

```json
{
  "name": "我的应用",
  "display_name": "我的应用",
  "version": "1.0.0",
  "publisher": "我的公司",
  "entry": "main.py",
  "icon": "assets/icon.ico",
  "license": "LICENSE",
  "readme": "README.md",
  "onefile": true,
  "platform_specific": {
    "windows": {
      "additional_pyinstaller_args": "--noconsole --uac-admin --add-data assets;assets --add-data config;config",
      "installer_options": {
        "languages": ["ChineseSimplified", "English"],
        "create_desktop_icon": true,
        "allow_run_after_install": true,
        "require_admin": true,
        "custom_inno_script": "custom.iss"
      }
    }
  }
}
```

## 常见问题

### 1. "无法定位程序输入点于动态链接库"错误

**解决方案**：
- 确保包含所有必要的DLL文件
- 使用`--add-binary`选项添加DLL文件
- 安装Visual C++ Redistributable包

### 2. 应用图标未显示

**解决方案**：
- 确保图标文件是有效的.ico格式
- 使用`--icon`参数指定图标路径
- 检查图标文件分辨率（建议包含多种分辨率）

### 3. 找不到资源文件

**解决方案**：
- Windows中使用分号(;)作为路径分隔符，而不是冒号(:)
- 示例：`--add-data assets;assets`
- 检查代码中的资源文件路径处理

### 4. 安装程序中文显示乱码

**解决方案**：
- 在installer_options中添加languages选项：`"languages": ["ChineseSimplified"]`
- 确保文本文件使用UTF-8编码

### 5. Windows Defender报毒

**解决方案**：
- 提交程序到微软进行验证
- 购买代码签名证书并签名应用
- 添加程序到Windows Defender排除列表 