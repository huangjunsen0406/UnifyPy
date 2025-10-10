# UnifyPy 2.0

> 专业的跨平台Python应用打包解决方案

## 🚀 项目简介

UnifyPy 2.0 是一个企业级跨平台Python应用打包工具，支持将Python项目打包为Windows、macOS、Linux平台的原生安装包。

### ✨ 核心特性

- **🔄 多平台支持（64位）**: Windows (EXE)、macOS (DMG)、Linux (DEB+RPM)
- **⚡ 并行构建**: 支持多格式并行生成，显著提升构建效率
- **🛡️ 企业级功能**: 自动回滚、会话管理、智能错误处理
- **🎨 优秀体验**: Rich进度条、分阶段显示、详细日志
- **🔧 完整配置**: 支持30+PyInstaller参数，JSON配置化
- **📦 自动化工具**: 第三方工具自动下载和管理
- **🍎 macOS权限管理**: 自动生成权限文件、代码签名支持
- **📊 智能路径处理**: 相对路径自动解析为绝对路径
- **🧩 插件化架构**: 基于事件总线与引擎的插件系统，支持外部插件扩展

## 📦 安装

### 系统要求
- Python 3.8+
- Windows 10+ / macOS 10.14+ / Linux (Ubuntu 18.04+)

### 安装 UnifyPy

```bash
pip install unifypy
```

### 平台特定工具

- **Windows**: Inno Setup（自动检测）
- **macOS**: create-dmg（内置）、Xcode Command Line Tools
- **Linux**: dpkg-dev、rpm-build、fakeroot（按需自动安装指导）

## 🚀 快速开始

### 基本用法

```bash
# 使用配置文件打包
unifypy . --config build.json

# 命令行快速打包
unifypy . --name myapp --version 1.0.0 --entry main.py --onefile

# 多格式并行构建
unifypy . --config build_multiformat.json --parallel --max-workers 4

# 详细输出模式
unifypy . --config build.json --verbose

# 清理重新构建
unifypy . --config build.json --clean --verbose

# 只生成可执行文件，跳过安装包
unifypy . --config build.json --skip-installer

# 指定特定格式
unifypy . --config build.json --format dmg --parallel

# macOS开发模式（自动权限配置）
unifypy . --config build.json --development --verbose

# 仅预检（不构建）
unifypy . --config build.json --dry-run
```

### 配置文件示例

创建 `build.json` 配置文件：

```json
{
  "name": "MyApp",
  "display_name": "我的应用程序", 
  "version": "1.0.0",
  "publisher": "我的公司",
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
      "microphone_usage_description": "需要麦克风权限进行语音功能",
      "camera_usage_description": "需要摄像头权限进行视频功能",
      "dmg": {
        "volname": "MyApp 安装器",
        "window_size": [600, 400],
        "icon_size": 100
      }
    },
    "linux": {
      "deb": {
        "package": "myapp",
        "depends": ["python3 (>= 3.8)", "libgtk-3-0"],
        "description": "我的Python应用程序"
      },
      "rpm": {
        "summary": "我的Python应用程序",
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

## 🔧 命令行参数

### 基本语法
```bash
unifypy <project_dir> [选项]
```

### 基本信息参数
| 参数 | 说明 | 示例 |
|------|------|------|
| `project_dir` | Python项目根目录路径（必需） | `. 或 /path/to/project` |
| `--config CONFIG` | 配置文件路径 (JSON格式) | `--config build.json` |
| `--name NAME` | 应用程序名称 | `--name MyApp` |
| `--display-name DISPLAY_NAME` | 应用程序显示名称 | `--display-name "我的应用"` |
| `--entry ENTRY` | 入口Python文件 | `--entry main.py` |
| `--version VERSION` | 应用程序版本 | `--version 1.0.0` |
| `--publisher PUBLISHER` | 发布者名称 | `--publisher "我的公司"` |

### 文件和资源参数
| 参数 | 说明 | 示例 |
|------|------|------|
| `--icon ICON` | 图标文件路径 | `--icon assets/app.png` |
| `--license LICENSE` | 许可证文件路径 | `--license LICENSE.txt` |
| `--readme README` | 自述文件路径 | `--readme README.md` |
| `--hooks HOOKS` | 运行时钩子目录 | `--hooks hooks/` |

### PyInstaller选项
| 参数 | 说明 | 示例 |
|------|------|------|
| `--onefile` | 生成单文件模式的可执行文件 | `--onefile` |
| `--windowed` | 窗口模式（不显示控制台） | `--windowed` |
| `--console` | 控制台模式 | `--console` |

### 构建控制选项
| 参数 | 说明 | 示例 |
|------|------|------|
| `--skip-exe` | 跳过可执行文件构建 | `--skip-exe` |
| `--skip-installer` | 跳过安装程序构建 | `--skip-installer` |
| `--clean` | 清理之前的构建文件 | `--clean` |
| `--format FORMAT` | 指定输出格式 | `--format dmg` |

### 工具路径选项
| 参数 | 说明 | 示例 |
|------|------|------|
| `--inno-setup-path INNO_SETUP_PATH` | Inno Setup可执行文件路径 | `--inno-setup-path /path/to/ISCC.exe` |

### 输出控制选项
| 参数 | 说明 | 示例 |
|------|------|------|
| `--verbose, -v` | 显示详细输出 | `--verbose` 或 `-v` |
| `--quiet, -q` | 静默模式 | `--quiet` 或 `-q` |

### 性能优化选项
| 参数 | 说明 | 示例 |
|------|------|------|
| `--parallel` | 启用并行构建 | `--parallel` |
| `--max-workers MAX_WORKERS` | 最大并行工作线程数 | `--max-workers 4` |

### 回滚系统选项
| 参数 | 说明 | 示例 |
|------|------|------|
| `--no-rollback` | 禁用自动回滚 | `--no-rollback` |
| `--rollback SESSION_ID` | 执行指定会话的回滚 | `--rollback abc123` |
| `--list-rollback` | 列出可用的回滚会话 | `--list-rollback` |

### macOS开发选项
| 参数 | 说明 | 示例 |
|------|------|------|
| `--development` | 强制开发版本（启用调试权限） | `--development` |
| `--production` | 生产版本（禁用调试权限，仅用于签名应用） | `--production` |

### 帮助选项
| 参数 | 说明 | 示例 |
|------|------|------|
| `-h, --help` | 显示帮助信息并退出 | `--help` |

## 📋 支持的打包格式

### Windows
- **EXE** (Inno Setup) - 标准安装程序

### macOS  
- **DMG** - 磁盘映像安装包

### Linux
- **DEB** - Debian/Ubuntu包
- **RPM** - Red Hat/CentOS包

## ⚙️ 配置文件详解

### 全局配置
```json
{
  "name": "应用名称",
  "display_name": "显示名称", 
  "version": "版本号",
  "publisher": "发布者",
  "entry": "入口文件",
  "icon": "图标文件",
  "license": "许可证文件",
  "readme": "说明文件"
}
```

### PyInstaller配置
```json
{
  "pyinstaller": {
    "onefile": false,
    "windowed": true,
    "clean": true,
    "noconfirm": true,
    "optimize": 2,
    "strip": true,
    "add_data": ["源路径:目标路径"],
    "hidden_import": ["模块名"],
    "exclude_module": ["排除的模块"]
  }
}
```

### macOS特定配置
```json
{
  "platforms": {
    "macos": {
      "bundle_identifier": "com.company.app",
      "minimum_system_version": "10.14.0",
      "category": "public.app-category.productivity",
      
      "microphone_usage_description": "需要麦克风权限进行语音功能",
      "camera_usage_description": "需要摄像头权限进行视频功能",
      
      "dmg": {
        "volname": "安装器名称",
        "window_size": [600, 400],
        "icon_size": 100
      }
    }
  }
}
```

## 🔄 并行构建

UnifyPy 2.0 支持多格式并行构建，显著提升构建效率：

```bash
# 启用并行构建
unifypy . --config build_multiformat.json --parallel

# 指定工作线程数
unifypy . --parallel --max-workers 4

# 查看并行构建效果
unifypy . --config build_comprehensive.json --parallel --verbose
```

## 🛡️ 回滚系统

自动跟踪构建操作，支持一键回滚：

```bash
# 列出可用的回滚会话
unifypy . --list-rollback

# 执行回滚
unifypy . --rollback SESSION_ID

# 禁用自动回滚
unifypy . --config build.json --no-rollback
```

## 🍎 macOS 特殊功能

### 自动权限管理
UnifyPy 2.0 为 macOS 应用提供了完整的权限管理方案：

```bash
# 开发模式 - 自动生成权限文件，适合开发和测试
unifypy . --config build.json --development

# 生产模式 - 用于已签名应用
unifypy . --config build.json --production
```

### 权限配置示例
```json
{
  "platforms": {
    "macos": {
      "bundle_identifier": "com.company.myapp",
      "microphone_usage_description": "需要麦克风权限进行语音功能",
      "camera_usage_description": "需要摄像头权限进行视频功能", 
      "location_usage_description": "需要位置权限提供基于位置的服务"
    }
  }
}
```

### 自动化功能
- ✅ 自动生成 entitlements.plist
- ✅ 自动更新 Info.plist 权限描述  
- ✅ 自动 ad-hoc 代码签名
- ✅ 自动图标格式转换（PNG → ICNS）

## 🔄 智能路径处理

UnifyPy 2.0 解决了跨目录打包时的路径问题：

### 问题场景
```bash
# 从 UnifyPy 目录打包其他项目
cd /path/to/UnifyPy
unifypy ../my-project --config ../my-project/build.json
```

### 智能解决方案
配置文件中的相对路径会自动解析为相对于**目标项目目录**：
- ✅ `"icon": "assets/icon.png"` → `/path/to/my-project/assets/icon.png`  
- ✅ `"add_data": ["data:data"]` → `/path/to/my-project/data:data`
- ✅ 支持嵌套配置和平台特定路径

### 支持的路径字段
- 单文件：`icon`, `license`, `readme`, `entry`, `setup_icon`, `version_file`
- 数组字段：`add_data`, `add_binary`, `datas`, `binaries`
- 格式：支持 `source:dest` 和 `source;dest` 两种分隔符

## 🏗️ 架构设计

UnifyPy 2.0 采用基于事件驱动的插件化架构设计：

### 核心架构组件

**引擎（Engine）+ 事件总线（EventBus）**

UnifyPy 2.0 的核心采用引擎驱动的插件化架构，通过事件总线协调各个插件的生命周期：

```python
# 构建生命周期事件
ON_START → HANDLE_ROLLBACK_COMMANDS → LOAD_CONFIG →
ENVIRONMENT_CHECK → PREPARE → BUILD_EXECUTABLE →
GENERATE_INSTALLERS → ON_SUCCESS → ON_EXIT
```

**插件系统（Plugin System）**

所有功能均以插件形式实现，支持优先级控制和外部插件扩展：

```python
class MyPlugin(BasePlugin):
    name = "my_plugin"
    priority = 50  # 数值越小优先级越高

    def register(self, bus: EventBus):
        bus.subscribe(ON_START, self.on_start, priority=self.priority)
        bus.subscribe(BUILD_EXECUTABLE, self.on_build, priority=self.priority)
```

**外部插件支持**

在配置文件中声明外部插件：

```json
{
  "plugins": [
    "my_package.my_plugin:MyPlugin",
    "company.custom_plugin:CustomPlugin"
  ]
}
```

### 核心设计模式

**注册表模式 (Registry Pattern)**
```python
# 动态注册和查找打包器
packager_registry = PackagerRegistry()
packager_class = packager_registry.get_packager("macos", "dmg")
```

**策略模式 (Strategy Pattern)**
```python
# 每个打包器实现特定格式的打包策略
class DMGPackager(BasePackager):
    def package(self, format_type, source_path, output_path):
        # DMG特定的打包逻辑
```

**事件驱动模式 (Event-Driven Pattern)**
```python
# 插件通过订阅事件来响应构建流程的不同阶段
bus.subscribe(PREPARE, self.prepare_build, priority=10)
bus.subscribe(BUILD_EXECUTABLE, self.build, priority=50)
```

### 核心组件交互

```mermaid
graph TD
    A[Engine 引擎] --> B[EventBus 事件总线]
    A --> C[BuildContext 构建上下文]

    B --> D[ProgressPlugin 进度插件]
    B --> E[ConfigPlugin 配置插件]
    B --> F[PyInstallerPlugin PyInstaller插件]
    B --> G[PackagingPlugin 打包插件]
    B --> H[RollbackPlugin 回滚插件]
    B --> I[外部插件...]

    E --> J[ConfigManager 配置管理]
    J --> K[路径解析]

    G --> L[PackagerRegistry 打包器注册表]
    L --> M[WindowsPackager]
    L --> N[MacOSPackager]
    L --> O[LinuxPackager]

    H --> P[RollbackManager 回滚管理器]
```

### 构建流程

1. **初始化阶段 (ON_START)**
   - 初始化进度管理器
   - 创建构建上下文
   - 加载外部插件

2. **配置加载阶段 (LOAD_CONFIG)**
   - 解析命令行参数
   - 加载和合并配置文件
   - 智能路径解析（相对→绝对）

3. **环境检查阶段 (ENVIRONMENT_CHECK)**
   - 验证项目结构和依赖
   - 检查工具可用性
   - 平台兼容性检查

4. **准备阶段 (PREPARE)**
   - 创建构建目录和临时文件
   - 初始化回滚系统
   - macOS 权限文件自动生成

5. **可执行文件构建 (BUILD_EXECUTABLE)**
   - PyInstaller 配置构建
   - 图标格式自动转换
   - macOS Info.plist 更新和代码签名

6. **安装包生成 (GENERATE_INSTALLERS)**
   - 根据平台选择合适的打包器
   - 支持并行构建多种格式
   - 自动验证输出文件

7. **成功完成 (ON_SUCCESS)**
   - 显示构建结果摘要
   - 输出文件清单

8. **退出清理 (ON_EXIT)**
   - 清理临时文件
   - 保存回滚数据
   - 关闭进度管理器

## 📁 项目结构

```
UnifyPy/
├── pyproject.toml        # 项目配置和依赖
├── build.json           # 标准配置示例
└── unifypy/            # 源代码包
    ├── __main__.py     # CLI 入口点
    ├── cli/            # 命令行接口
    ├── core/           # 核心模块（engine、event_bus、plugin、config...）
    ├── plugins/        # 内置插件（progress、config、pyinstaller、packaging...）
    ├── platforms/      # 平台打包器（windows、macos、linux）
    ├── pyinstaller/    # PyInstaller 集成
    ├── templates/      # 模板文件
    ├── tools/          # 内置工具
    └── utils/          # 工具模块
```

## 🔍 故障排除

### 常见问题

**Q: PyInstaller打包失败？**
```bash
# 检查依赖
pip install pyinstaller>=5.0

# 清理重试
unifypy . --config build.json --clean --verbose
```

**Q: macOS权限配置问题？**
```bash
# 使用开发模式自动生成权限文件
unifypy . --config build.json --development --verbose

# 检查生成的权限文件
cat auto_generated_entitlements.plist
```
- 检查配置文件中的权限描述
- 确保Bundle ID格式正确（com.company.appname）
- 参考 `build_macos_permissions_example.json`

**Q: Linux依赖缺失？**
```bash
# Ubuntu/Debian
sudo apt-get install dpkg-dev fakeroot

# CentOS/RHEL  
sudo yum install rpm-build
```

**Q: 并行构建失败？**
```bash
# 减少工作线程数
unifypy . --parallel --max-workers 2

# 或禁用并行构建
unifypy . --config build.json
```

**Q: 配置文件中的路径找不到？**
```bash
# 确保相对路径是相对于项目目录的
# ✅ 正确：项目在 /path/to/myapp，图标在 /path/to/myapp/assets/icon.png
"icon": "assets/icon.png"

# ❌ 错误：使用相对于UnifyPy目录的路径
"icon": "../myapp/assets/icon.png" 

# 检查路径解析
unifypy . --config build.json --verbose
```

### 调试技巧

1. **启用详细输出**: `--verbose`
2. **检查日志**: 查看构建过程详细信息
3. **单步构建**: 使用 `--skip-exe` 或 `--skip-installer`
4. **回滚测试**: 使用 `--list-rollback` 查看历史
5. **路径问题**: 检查配置文件中的相对路径是否正确
6. **权限问题**: macOS使用 `--development` 模式进行调试

## 📝 最佳实践

### 配置文件管理
- 使用不同环境的配置文件（开发、测试、生产）
- 版本控制中包含配置文件模板
- 敏感信息使用环境变量

### 构建优化
- 启用并行构建提升效率
- 合理配置 `exclude_module` 减小包体积
- 使用 `clean` 确保构建环境干净

### 跨平台兼容
- 路径分隔符使用 `/` 或自动处理
- 图标格式让工具自动转换（PNG→ICNS/ICO）
- 测试不同平台的依赖兼容性
- **重要**: 配置文件中的相对路径会自动解析为相对于项目目录的绝对路径

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

UnifyPy 2.0 - 让Python应用打包变得简单高效 🚀
