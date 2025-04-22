# Python项目通用打包工具

这是一个通用的Python项目打包工具，可以将任何Python项目打包成独立的可执行文件和Windows安装程序。

## 功能特点

- 自动打包Python项目为单文件可执行程序（使用PyInstaller）
- 自动生成Windows安装程序（使用Inno Setup）
- 支持自定义应用名称、版本、图标等
- 自动检测并安装所需的依赖工具
- 支持包含自定义钩子、资源文件
- 支持自定义许可证文件和自述文件
- 支持JSON配置文件方式配置打包参数
- 一键完成整个打包流程

## 安装要求

- Python 3.6或更高版本
- 联网环境（首次使用时需要下载依赖）
- Windows操作系统（仅安装程序生成部分需要）

## 目录结构

```
python_packager/
├── package_python.py     # 主打包脚本
├── README.md             # 说明文档
├── templates/            # 模板目录
│   └── setup.iss.template # Inno Setup脚本模板
└── tools/                # 工具脚本目录
    ├── build_exe.py      # 可执行文件构建工具
    ├── build_installer.py # 安装程序构建工具
    └── create_icon.py    # 图标生成工具
```

## 使用方法

### 基本用法

将项目打包为可执行文件和安装程序：

```bash
python package_python.py 你的项目路径
```

这将使用默认配置打包你的项目，入口文件默认为`main.py`，应用名称默认为项目目录名称。

### 高级用法

```bash
python package_python.py 你的项目路径 --name "应用名称" --entry app.py --version "1.2.3" --publisher "发布者名称" --icon path/to/icon.ico --hooks hooks目录
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| project_dir | Python项目根目录路径 | (必填) |
| --name | 应用程序名称 | 项目目录名称 |
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

### 使用配置文件

你也可以通过JSON配置文件指定打包参数：

```json
{
  "name": "我的应用",
  "entry": "app.py",
  "version": "1.2.3",
  "publisher": "我的公司",
  "icon": "assets/icon.ico",
  "license": "LICENSE.txt",
  "readme": "README.md",
  "hooks": "hooks"
}
```

然后使用以下命令打包：

```bash
python package_python.py 你的项目路径 --config config.json
```

## 打包过程说明

打包过程分为以下几个步骤：

1. **环境准备**：检查项目目录，创建临时工作目录，准备模板文件
2. **构建可执行文件**：使用PyInstaller将项目打包为独立可执行文件
3. **构建安装程序**：使用Inno Setup将可执行文件打包为Windows安装程序
4. **清理临时文件**：删除打包过程中生成的临时文件

## 安装程序功能

生成的Windows安装程序具有以下功能：

- 标准的Windows安装界面
- 支持中文和英文安装界面
- 可选创建桌面快捷方式
- 可选设置开机自动启动
- 完整的卸载功能
- 安装完成后可选择立即启动程序

## 常见问题解决

### 找不到PyInstaller
如果出现找不到PyInstaller的错误，程序会自动尝试安装。如果安装失败，请手动执行：
```bash
pip install pyinstaller
```

### 找不到Inno Setup
如果找不到Inno Setup，程序会自动下载并安装。如安装失败，请手动下载Inno Setup并安装。

### 生成的可执行文件过大
这是因为PyInstaller会包含所有依赖库。可以尝试添加`--additional "--exclude-module <模块名>"`参数排除不需要的模块。

### 安装程序生成失败
请检查setup.iss文件是否有语法错误，以及是否有权限创建安装程序文件。

## 自定义钩子

钩子目录可以包含在打包过程中需要执行的自定义Python脚本。这些脚本将被打包到可执行文件中，并在运行时执行。

## 许可协议

本工具使用MIT许可证发布，详见LICENSE文件。 