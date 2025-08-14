# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 重要说明

**请始终使用中文回答**：在处理此项目时，所有回复和解释都应该使用中文，以便与项目的中文开发环境保持一致。

## 项目概述

UnifyPy 2.0 是一个专业的跨平台 Python 应用打包解决方案，可将 Python 项目转换为 Windows、macOS 和 Linux 平台的原生安装包。2.0 版本采用了全新的模块化架构设计，具备企业级功能和全面的打包格式支持。

## 常用开发命令

### 基本使用
```bash
# 使用配置文件进行打包
python main.py . --config build.json

# 使用命令行参数快速打包
python main.py /path/to/project --name myapp --version 1.0.0 --entry main.py

# 跳过可执行文件生成（仅生成安装包）
python main.py . --config build.json --skip-exe

# 跳过安装包生成（仅生成可执行文件）
python main.py . --config build.json --skip-installer

# 生成单文件可执行文件并显示详细输出
python main.py . --config build.json --onefile --verbose

# 启用并行构建支持多种格式
python main.py . --config build.json --parallel --max-workers 4

# 清理之前的构建
python main.py . --config build.json --clean

# macOS 开发模式（启用调试权限）
python main.py . --config build.json --development
```

### 回滚和会话管理
```bash
# 列出可用的回滚会话
python main.py . --list-rollback

# 执行指定会话的回滚
python main.py . --rollback SESSION_ID

# 禁用自动回滚
python main.py . --config build.json --no-rollback
```

### 测试和验证
```bash
# 测试配置加载
python -c "from src.core.config import ConfigManager; ConfigManager('build.json')"

# 测试打包器注册表
python -c "from src.platforms.registry import PackagerRegistry; registry = PackagerRegistry(); print(registry.get_all_platforms())"

# 验证 PyInstaller 配置构建
python -c "from src.pyinstaller.config_builder import PyInstallerConfigBuilder; builder = PyInstallerConfigBuilder()"

# 测试进度系统
python -c "from src.utils.progress import ProgressManager; pm = ProgressManager(); pm.start()"
```

## 架构概览 (UnifyPy 2.0)

UnifyPy 2.0 采用了全新设计的模块化架构，在 `src/` 目录下进行了清晰的关注点分离。

### 核心设计模式

- **注册表模式**: `PackagerRegistry` 动态管理平台特定的打包器
- **工厂模式**: 通过注册表查找创建平台打包器
- **策略模式**: 每个打包器实现特定格式的打包策略
- **建造者模式**: `PyInstallerConfigBuilder` 构建复杂配置
- **命令模式**: `CommandRunner` 封装构建操作并支持回滚

### 核心组件

#### 主入口点 (`main.py`)

- `UnifyPyBuilder` 类协调整个构建过程
- 参数解析和全面的选项支持
- 环境验证和准备
- 进度跟踪和错误处理
- 回滚会话管理

#### 核心配置系统 (`src/core/`)

- `ConfigManager`: 处理配置加载、合并和验证
- `Environment`: 平台检测和环境设置
- 支持配置层次: 命令行参数 > 平台配置 > 全局配置 > 默认配置
- 多格式配置和平台特定覆盖

#### 平台打包 (`src/platforms/`)

- `BasePackager`: 定义打包器接口的抽象基类
- `PackagerRegistry`: 打包器的动态注册和查找
- 平台特定实现:
  - `windows/`: Inno Setup (EXE) 和 MSI 打包器
  - `macos/`: DMG、PKG 和 ZIP 打包器
  - `linux/`: DEB、RPM、AppImage 和 TarGZ 打包器

#### PyInstaller 集成 (`src/pyinstaller/`)

- `PyInstallerConfigBuilder`: 构建 PyInstaller 命令配置
- `Builder`: 处理 PyInstaller 执行和输出管理
- 支持 30+ PyInstaller 参数的完整配置映射

#### 工具系统 (`src/utils/`)

- `ProgressManager`: 基于 Rich 的进度跟踪和阶段管理
- `CommandRunner`: 静默/详细命令执行和错误处理
- `ParallelBuilder`: 多种格式的多线程构建
- `RollbackManager`: 自动回滚和会话跟踪
- `ToolManager`: 自动工具检测和管理
- `FileOperations`: 安全文件操作和清理

### 配置系统

UnifyPy 2.0 使用分层 JSON 配置系统，支持平台特定配置节：

```json
{
  "name": "MyApp",
  "version": "1.0.0",
  "entry": "main.py",
  "pyinstaller": {
    "onefile": false,
    "windowed": true,
    "add_data": ["assets:assets"],
    "hidden_import": ["requests", "json"]
  },
  "platforms": {
    "windows": {
      "pyinstaller": {
        "add_data": ["assets;assets"]
      },
      "inno_setup": {
        "create_desktop_icon": true,
        "languages": ["english", "chinesesimplified"]
      }
    },
    "macos": {
      "pyinstaller": {
        "osx_bundle_identifier": "com.example.myapp"
      },
      "create_dmg": {
        "volname": "MyApp 安装器",
        "window_size": [600, 400]
      }
    },
    "linux": {
      "deb": {
        "package": "myapp",
        "depends": ["python3 (>= 3.8)"]
      },
      "appimage": {
        "desktop_entry": true
      }
    }
  }
}
```

### 支持的打包格式

- **Windows**: EXE (Inno Setup)、MSI
- **macOS**: DMG、PKG、ZIP
- **Linux**: DEB、RPM、AppImage、TAR.GZ

### 构建流程

1. **初始化**: 解析参数，加载/合并配置
2. **验证**: 检查项目结构、依赖项、磁盘空间
3. **环境设置**: 创建构建目录，准备工具
4. **PyInstaller 构建**: 使用平台特定参数生成可执行文件
5. **包生成**: 使用注册的打包器创建安装程序
6. **验证**: 验证输出并显示结果
7. **清理**: 删除临时文件，维护回滚数据

### 企业级功能

#### 回滚系统

- 使用唯一 ID 自动跟踪会话
- 支持回滚的安全文件操作
- 会话列表和手动回滚执行
- 可配置的回滚策略

#### 并行构建

- 不同格式的多线程包生成
- 优化的资源利用
- 可配置的工作池大小
- 跨并行任务的进度聚合

#### 工具管理

- 自动检测所需的第三方工具
- 智能工具下载和安装指导
- 版本兼容性检查
- 平台特定的工具处理

## 平台要求

### Windows

- Python 3.8+
- PyInstaller >= 5.0
- Inno Setup（自动检测或通过 `--inno-setup-path` 指定）

### macOS

- Python 3.8+
- PyInstaller >= 5.0
- create-dmg（捆绑在 `tools/create-dmg/` 中）
- 用于 PKG 生成的 Xcode 命令行工具

### Linux

- Python 3.8+
- PyInstaller >= 5.0
- 格式特定工具（自动下载）：
  - DEB: `dpkg-dev`、`fakeroot`
  - RPM: `rpm-build`
  - AppImage: `appimagetool`、`linuxdeploy`
