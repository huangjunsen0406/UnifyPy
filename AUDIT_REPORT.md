# UnifyPy 整体项目审计报告

| 项 | 内容 |
|----|------|
| **项目** | UnifyPy — 跨平台 Python 应用打包工具 |
| **审计日期** | 2026-07-23（初稿）；**2026-07-25 更新**（从入口全链路 + 配置/冗余深挖） |
| **当前版本** | `pyproject.toml` = **2.0.17**；`unifypy/__init__.py` = **2.0.0**（不一致） |
| **代码量** | 约 12.3k LOC Python（不含 create-dmg 子树） |
| **范围** | 从 CLI 入口走通主路径；配置合并；插件生命周期；平台/工具；发布与工程化 |
| **方法** | 只读代码审阅 + 入口时序追踪 + 交叉核对 |

---

## 1. 执行摘要

UnifyPy 作为 **「配置驱动的跨平台打包编排层」**（PyInstaller + Win/macOS/Linux 安装器），方向正确，插件化生命周期与平台覆盖已具备产品雏形。

当前最大短板 **不是缺功能**，而是：

1. **零业务自动化测试 + CI 只发布不测** → 回归全靠手工  
2. **安全默认值偏松**（无哈希下载后执行、可选 `sudo` 装包、`shell=True` 默认）  
3. **版本 / 路径 / 配置 / 平台命名契约不统一**  
4. **入口层冗余与半废弃抽象**（双 CacheManager、双平台命名、`EnvironmentManager(".")`、`--quiet` 未接线）  
5. **若干正确性边角**（RPM `env`、macOS 校验、默认 development entitlements）

**优先建议**：入口契约收紧 + 测试地基 + 安全默认 + 去冗余，再谈产品化扩展。

---

## 2. 从入口走通：调用链与问题

### 2.1 正常构建时序

```
unifypy [project_dir] [flags]
  └─ __main__.main()
       ├─ ArgumentParser.parse_arguments()
       ├─ [可选] --init → InteractiveWizard → 改写 args.config / args.clean
       ├─ BuildContext(args)          # project_dir.resolve()
       ├─ Engine(context, PluginManager)
       │    └─ setup() → load_builtin_plugins + register
       └─ engine.run()
            EventBus 顺序:
              ON_START
                ProgressPlugin → progress
                DryRunPlugin   → 若 dry_run: skip_exe + skip_installer
                AutoRollback   → RollbackManager
              HANDLE_ROLLBACK_COMMANDS  (list/rollback 则 should_exit)
              LOAD_CONFIG
                ConfigPlugin   → ConfigManager + CacheManager + ensure dist/installer
                ExternalPluginsLoader → importlib 加载 plugins[]
              ENVIRONMENT_CHECK
                EnvironmentPlugin → 入口文件、架构、PyInstaller、按格式工具
                WindowsLanguagePlugin
              PREPARE
                AutoRollback 包装 file_ops
                PreparePlugin → temp、clean、配置 hash、剔除无效 icon
              BUILD_EXECUTABLE
                PyInstallerPlugin → spec + pyinstaller + macOS 后处理
              GENERATE_INSTALLERS
                PackagingPlugin → formats → packager.package
              ON_SUCCESS → Summary / 清理 rollback 会话
              ON_ERROR   → 回滚 + progress 打印 errors
              ON_EXIT    → cleanup temp + progress.stop
```

### 2.2 入口层问题（CLI / `__main__` / Context）

| ID | 问题 | 位置 | 影响 / 建议 |
|----|------|------|-------------|
| E-1 | **帮助文案过时** | `argument_parser.py:28-33` epilog 写 `python main.py` | 应改为 `unifypy`；回滚提示同样写 `python main.py`（`rollback_plugin.py:38`） |
| E-2 | **`--format` 帮助漏 appimage** | `argument_parser.py:163` 写 `(exe,dmg,deb,rpm)` | 与 registry/wizard 不一致；补 `appimage` |
| E-3 | **`--quiet` 完全未接线** | 仅 argparse 定义；业务路径无读取 | 死参数；应接到 Progress 或删除 |
| E-4 | **`--verbose` / `--quiet` 无互斥** | argparse 未 `mutually_exclusive` | 同时传时行为未定义 |
| E-5 | **`--development` / `--production` 语义反直觉** | `post_processor.py:69-76`：`development = not production or development or debug` | **默认即 development entitlements**（含调试相关权限）；仅 `--production` 才关。生产构建易误带开发权限。建议默认 production，开发需显式 `--development` |
| E-6 | **`--onefile`/`--windowed`/`--console` 只能打开不能关闭** | `action="store_true", default=None` | 无法用 CLI 强制关闭配置文件中的 `onefile: true`；缺 `--no-onefile` 等 |
| E-7 | **`--init` 强制 `args.clean = True`** | `__main__.py:35` | 用户选「立即构建」总是 clean；应可确认 |
| E-8 | **无 `--version` 显示工具版本** | argparse 无 | 与包版本分裂叠加，排障困难 |
| E-9 | **`project_dir` 必填** | 位置参数 | `unifypy --help` 外，`unifypy` 无参直接失败；可考虑默认 `.` |
| E-10 | **`BuildContext` 组件全 None** | `context.py` | 依赖插件填充顺序；无类型协议，插件写错字段静默失败 |

### 2.3 配置加载与合并（LOAD_CONFIG）

**设计意图**（`config.py`）：

```
默认 < 文件全局 < 平台通用键（排除安装器键） < CLI(_args_to_config)
get_pyinstaller_config 再叠：顶层通用键 < pyinstaller section < CLI 子集
```

| ID | 问题 | 位置 | 说明 |
|----|------|------|------|
| C-1 | **`vars(args)` 键名 vs 映射表** | `config_plugin.py:31` + `_args_to_config` | argparse 的 `display_name` 来自 `--display-name`（dest 默认 `display_name`）✅ 当前一致；但 `vars` 会把 **全部** CLI 字段塞进 `self.args`，含 `project_dir/verbose/parallel/...`，hash 过滤靠 CacheManager 白名单，脆弱 |
| C-2 | **顶层 `onefile` 与 `pyinstaller.onefile` 双轨** | 默认配置顶层 `onefile: False`；示例 JSON 写在 `pyinstaller` 内 | `get_pyinstaller_config` 先抄顶层再 merge section，行为可用但文档/示例易混淆 |
| C-3 | **`preprocess_paths` 仅打包阶段调用** | `packaging_plugin.py:56` | PyInstaller spec 路径策略与安装器绝对路径策略分裂；入口/icon 校验用 `resolve_path` 不改写配置 |
| C-4 | **配置校验失败用 `print` 警告** | `config.py:422` | 不进 progress/logging；CI 难收集 |
| C-5 | **配置路径不相对 `project_dir` 解析** | `ConfigManager(config_path=ctx.args.config)` | `--config build.json` 相对 **cwd** 而非 project_dir；跨目录调用易「找不到配置」 |
| C-6 | **`platform_specific` 旧键仍兼容** | `_get_platform_config` | 双格式并存合理；缺 deprecation 警告 |
| C-7 | **无 JSON Schema / 未知键警告** | — | 错别字配置静默忽略 |
| C-8 | **示例配置冗余字段** | `build.json` 等 | 同时写 `bundle_identifier` 与 `osx_bundle_identifier`；`inno_setup.app_name` 与顶层 `display_name` 重复，易漂移 |

### 2.4 插件生命周期冗余与缺口

| ID | 问题 | 说明 |
|----|------|------|
| P-A | **`dist`/`installer` 目录创建两次** | `ConfigPlugin` 与 `PreparePlugin` 都 `ensure_dir`；`--clean` 时再删再建 |
| P-B | **格式列表逻辑重复** | `PackagingPlugin._get_requested_formats` ≈ `EnvironmentPlugin._get_formats_from_config` | 应抽 `FormatResolver` |
| P-C | **`DryRunPlugin` 只改 skip 标志** | 仍跑满 ENVIRONMENT_CHECK + PREPARE（含工具检测）；文档说「预检」OK，但会触发工具自动安装路径 |
| P-D | **`ExternalPluginsLoader` 挂在 LOAD_CONFIG** | 依赖 Config 已成功；失败只 warning，继续构建 |
| P-E | **`SummaryPlugin` 产物路径与 macOS 不一致** | onedir 用 `dist/name`；macOS 实际可能是 `display_name.app`，摘要可能漏报 |
| P-F | **`CleanupPlugin` 吞异常** | `except Exception: pass` |
| P-G | **EventBus 同事件失败不中断** | 一个 handler 挂了，同事件后续仍跑 |

### 2.5 环境与平台命名分裂（高优先级冗余）

| 模块 | 平台键 | 架构键 |
|------|--------|--------|
| `core/platforms.py`（对外） | `windows` / `macos` / `linux` | `x64` / `arm64` |
| `core/environment.py`（对内） | `win` / `mac` / `linux` | 同上 + glibc/musl 后缀 |
| `ConfigManager.current_platform` | **macos 体系** | — |
| `EnvironmentManager.current_platform` | **mac 体系** | — |
| `BasePackager` | `normalize_platform()` → macos | 但 `env_manager = EnvironmentManager(".")` |

**问题：**

1. **两套平台字符串**（`mac` vs `macos`，`win` vs `windows`）并存，新人必踩。  
2. **`ctx.env_manager` 在 ConfigPlugin 用 `project_dir` 创建，但没有任何下游读 `ctx.env_manager`**；Packager 各自 `EnvironmentManager(".")`。  
3. **`EnvironmentManager(".")`**（`base.py:36`）→ `project_dir` 是 **进程 cwd**，不是用户项目根。Inno 搜 `ChineseSimplified.isl`、现代文件名等可能落错目录。  
4. `environment.py` ~513 行，大量 `get_modern_filename` / Rosetta / 示例字典；与精简的 `platforms.py` 职责重叠，**半废弃 API 表面大**。

**建议：** 对外统一 `windows|macos|linux`；Packager 注入 `project_dir`；收敛或删除未用的 modern-key 展示 API。

### 2.6 构建与打包阶段

| ID | 问题 | 位置 |
|----|------|------|
| B-1 | macOS `_verify_output` 查 `dist/name/name`，BUNDLE 实际为 `name.app` | `pyinstaller_plugin.py:134-142` |
| B-2 | `process_built_app` 只认 `dist/{app_name}.app`，与 onefile 分支不一致；display_name 重命名后路径变化 | `post_processor.py:110-137` |
| B-3 | `_update_info_plist` **有实现但主流程未调用**（权限依赖 spec BUNDLE） | `post_processor.py:155+` vs `process_built_app` |
| B-4 | 权限 key 映射复制 4+ 处 | config_builder / entitlements / info_plist / post_processor |
| B-5 | Packaging 并行路径调用 `optimize_pyinstaller_build` | 安装包阶段改配置，**不回头重建 exe**，近似死逻辑 |
| B-6 | RPM `env` 算了未传入 `run_command` | `rpm_packager.py:318-333` |
| B-7 | 双 `CacheManager` 类 | `utils/cache_manager.py` vs `parallel_builder.CacheManager`（`~/.unifypy_cache`，几乎未接入下载） |
| B-8 | 配置 hash 写死 `unifypy_version: "2.0.0"`；模板路径按源码树 `project_dir/unifypy/templates` | 安装后的 wheel 布局下模板变更检测失效 |
| B-9 | Prepare 对所有 platforms 预写 hash，与「只构建当前平台」不完全匹配 | `prepare_plugin.py:58-61` |

### 2.7 配置文件与仓库冗余

| 项 | 说明 |
|----|------|
| 多份示例 JSON | `build.json` / `build_comprehensive.json` / `build_multiformat.json` / `build_macos_permissions_example.json` / `py-xiaozhi.json` — 有价值，但缺「最小 CI fixture」与字段说明索引 |
| `requirements.txt` ∥ `pyproject` dependencies | 双源，易漂移 |
| `PERMISSIONS.md` + `PERMISSIONS_EN.md` + docs | 与代码内权限表三重维护 |
| `unifypy/image.png` | 未进包元数据，仓库噪音 |
| create-dmg examples/tests 进 sdist | MANIFEST `recursive-include tools *` |
| `.gitignore` 忽略 `.trellis` / `.claude` | 规范与任务难协作 |
| 无 CHANGELOG | 与 GitHub Release notes 脱节 |

---

## 3. 架构速览（组件表）

| 组件 | 路径 | 职责 |
|------|------|------|
| 入口 | `unifypy/__main__.py` | 参数、向导、Engine |
| 引擎 | `unifypy/core/engine.py` | 生命周期、退出码 |
| 事件总线 | `unifypy/core/event_bus.py` | 订阅/触发、errors 收集 |
| 配置 | `unifypy/core/config.py` | 加载、合并、校验、路径 |
| 平台常量 | `unifypy/core/platforms.py` | windows/macos/linux + x64/arm64 |
| 环境管理 | `unifypy/core/environment.py` | 架构/文件名/C 运行时（与 platforms 重叠） |
| 插件 | `unifypy/plugins/*` | 见 §2.1 |
| 平台打包 | `unifypy/platforms/*` | exe/dmg/deb/rpm/appimage |
| 工具 | `unifypy/utils/tool_manager.py` | 检测/下载/安装 |

### 3.1 结构性问题摘要

- EventBus 失败不 fail-fast  
- 巨型模块：config_builder / tool_manager / inno_setup  
- 路径策略分裂（相对 spec vs 绝对 preprocess）  
- 平台命名双轨 + EnvironmentManager 未注入 project_dir  
- 死参数 / 半死代码：`--quiet`、parallel CacheManager、部分 modern filename API  

---

## 4. 已知 Trellis 任务

| 任务 | 状态 | 说明 |
|------|------|------|
| `00-bootstrap-guidelines` | in_progress | `.trellis/spec` 仍多占位 |
| `05-15-fix-config-merge-and-tool-detection` | in_progress | 代码有修复痕迹；**缺测试与归档** |
| `05-18-fix-hardcoded-absolute-path-in-pyinstaller-spec-generation` | in_progress | entry 相对路径方向；其它绝对路径与测试仍欠 |

---

## 5. 优化项总表

### 5.1 P0 — 正确性 / 安全 / 入口契约

| ID | 项 | 参考位置 | 建议 |
|----|----|----------|------|
| P0-1 | 版本多源不一致 | pyproject / `__init__` / cache_manager | 单一来源；bump 同步 |
| P0-2 | 零自动化测试 + CI 无 test | — | 最小 tests + CI pytest/ruff |
| P0-3 | 下载无 SHA256；zip 无防护 | tool_manager | 固定版本 + 校验 + 安全解压 |
| P0-4 | 静默装 Inno / 执行 AppImage | tool_manager | 默认关；显式 flag |
| P0-5 | 无确认 sudo 装包 | tool_manager ~812 | 默认只打印命令 |
| P0-6 | RPM `env` 未传入 | rpm_packager.py:318-333 | `run_command(..., env=env)` |
| P0-7 | macOS 输出校验错误 | pyinstaller_plugin.py:134-142 | 校验 `.app` 布局 |
| P0-8 | 默认 development entitlements | post_processor.py:69-76 | 默认生产；开发显式开启 |
| P0-9 | `EnvironmentManager(".")` | platforms/base.py:36 | 注入真实 `project_dir` |
| P0-10 | 外部插件任意 import | external_plugins_loader | 白名单 / entry_points |
| P0-11 | 配置路径相对 cwd | ConfigPlugin | 相对 project_dir 解析 `--config` |

### 5.2 P1 — 去冗余 / 工程质量

| ID | 项 | 建议 |
|----|----|------|
| P1-1 | 统一平台命名 | 删除 win/mac 对内键或仅作 internal_key 映射层 |
| P1-2 | 合并/删除双 CacheManager | 只保留项目 `.unifypy` 或明确分工 |
| P1-3 | FormatResolver 单源 | 环境检测与打包共用 |
| P1-4 | 权限 key 单源 | 一处 mapping 模块 |
| P1-5 | `shell` 默认 False | command_runner.py:62 |
| P1-6 | 接线或删除 `--quiet` | Progress 静默 |
| P1-7 | CLI 文案与 `--format` 补全 | unifypy、appimage |
| P1-8 | 互斥 verbose/quiet；CLI 否定开关 | `--no-onefile` 等 |
| P1-9 | 目录创建/hash 逻辑收敛 | Config vs Prepare 职责划分 |
| P1-10 | AppID 不写回 build.json | 写 `.unifypy/metadata.json` |
| P1-11 | ISS/脚本注入与包名校验 | 转义 + DEB 正则 |
| P1-12 | 工程化 | ruff/mypy/pytest/pre-commit/CHANGELOG/urls |
| P1-13 | MANIFEST 瘦身 | 去掉 create-dmg tests/examples |
| P1-14 | 弃用 create-release@v1 | softprops/gh |
| P1-15 | 去掉并行路径无效 optimize | 或真正并入 exe 构建 |
| P1-16 | Summary / verify 统一产物路径 | 含 display_name.app |
| P1-17 | 调用未用的 `_update_info_plist` 或删死代码 | 行为单一 |
| P1-18 | requirements 与 pyproject 单源 | |

### 5.3 P2 — 体验 / 性能 / 产品化

| ID | 项 |
|----|-----|
| P2-1 | 配置 JSON Schema + 示例字段索引 |
| P2-2 | hash 含 entry 内容；模板用 importlib.resources |
| P2-3 | 库式 `build(config)` API 文档 |
| P2-4 | notarize / MSI / pkg 按需 |
| P2-5 | logging 统一；收窄 except |
| P2-6 | 拆三大巨石模块 |
| P2-7 | Trusted Publisher OIDC |
| P2-8 | 填满 Trellis spec；收口任务 |
| P2-9 | 交互向导与 Rich 统一 |
| P2-10 | `run_command` timeout + 下载重试 |

---

## 6. 安全检查摘要

| 项 | 结论 |
|----|------|
| 主路径 shell=False | ✅ 多数显式 |
| 默认 shell=True | ❌ |
| 下载校验 / Zip Slip | ❌ |
| sudo 自动装包 | ❌ |
| 静默执行安装器 | ❌ |
| 外部插件 | ⚠️ 配置即代码 |
| DEB/RPM/ISS 脚本注入 | ⚠️ 信任边界需文档 |
| 默认 development entitlements | ⚠️ 权限面偏大 |
| 硬编码密钥 | ✅ 未见 |

---

## 7. 测试与工程卫生

| 能力 | 现状 |
|------|------|
| 项目 pytest | **0** |
| CI test/lint | **无**（仅 publish） |
| pre-commit / ruff 入仓配置 | **无** |
| logging | **无标准 logging** |
| 类型注解 | 约半数+ 有部分注解；入口/plugin 偏弱 |
| CHANGELOG / dev extras | **无** |

### 建议首批测试

1. `test_config_merge.py` — CLI > 平台 > 全局；INSTALLER_KEYS  
2. `test_formats.py` — formats 列表优先  
3. `test_spec_paths.py` — 无机器绝对路径  
4. `test_config_path_resolve.py` — `--config` 相对 project_dir  
5. `test_packager_project_dir.py` — EnvironmentManager 非 cwd  
6. `test_verify_output_macos.py` — `.app`  
7. `test_rpm_env.py` — env 传入  
8. `test_entitlements_default.py` — production/development 默认  

---

## 8. 平台打包分评

### Windows（Inno）

- 优点：检测、ISS、中文语言包、AppID  
- 问题：写回 build.json；ISS 注入；env_manager 项目根错误；无 MSI/签名  

### macOS（DMG）

- 优点：create-dmg 内置；entitlements；display_name  
- 问题：默认 development；校验/摘要路径；`_update_info_plist` 未接入主流程；无公证  

### Linux

- 优点：deb/rpm/appimage 结构完整  
- 问题：RPM env；sudo 装工具；脚本注入；包名校验  

---

## 9. 发布与 PyPI

| 项 | 状态 |
|----|------|
| 入口脚本 | ✅ `unifypy` |
| 版本一致性 | ❌ |
| Publish CI | 有构建上传；无质量门禁；create-release 弃用 |
| MANIFEST | 偏胖（tools 全量） |
| 元数据 | 缺 urls / extras / 细分 classifiers |

---

## 10. 模块健康度

| 区域 | 评分 | 说明 |
|------|------|------|
| 入口 CLI | ⭐⭐⭐ | 能用；死参数、文案、开关语义 |
| Engine/Plugin | ⭐⭐⭐⭐ | 清晰；错误与重复 |
| Config | ⭐⭐⭐ | 强；契约与测试不足 |
| Environment vs Platforms | ⭐⭐ | 双轨冗余 |
| PyInstaller | ⭐⭐⭐ | 全；校验/路径 |
| 平台打包 | ⭐⭐⭐ | 能用；env/注入 |
| 工具管理 | ⭐⭐ | 安全债 |
| 测试/CI | ⭐ | 空白 |
| 文档（用户） | ⭐⭐⭐⭐ | 较好 |

---

## 11. 推荐落地路线

### 第 1 周（入口 + 止血）

1. P0：RPM env、macOS verify、版本单源、`EnvironmentManager(project_dir)`  
2. 默认 entitlements 改为 production 语义（或文档大红字 + CI 检查）  
3. `--config` 相对 project_dir；补 `--version`；修 help/format/quiet  
4. shell 默认 False；sudo/静默安装默认关；下载校验  
5. 最小 tests + CI  

### 第 2–4 周（去冗余）

6. FormatResolver；权限 key 单源；合并 CacheManager  
7. 平台命名统一；收敛 environment API  
8. 不写回 build.json；Summary 路径；删无效 optimize  
9. MANIFEST / create-release / 任务归档  

### 中期

10. 拆巨石模块；JSON Schema；logging；notarize 等  

---

## 12. 冗余清单（速查）

| 冗余 | 建议 |
|------|------|
| `platforms.py` vs `environment.py` 平台检测 | 单源 normalize_* |
| 双 `CacheManager` | 合并或改名隔离 |
| 双份 formats 推断 | FormatResolver |
| 多份权限 key map | 单模块 |
| Config + Prepare 重复 ensure_dir | 只在 Prepare |
| `ctx.env_manager` 创建后未用 | 注入 Packager 或删除 ctx 字段 |
| `parallel_builder.optimize_*` 装包期调用 | 删除或前移 |
| `_update_info_plist` 未调用 | 接入或删除 |
| `--quiet` 未使用 | 接线或删除 |
| requirements.txt ∥ pyproject | 单源 |
| 示例 JSON 字段重复 | schema + 生成文档 |
| create-dmg tests/examples 进包 | MANIFEST 排除 |
| 版本字符串 3 处 | 1 处 |

---

## 13. 结论

从 **`unifypy` 入口 → Engine → 配置 → 构建 → 安装包`** 全链路看：编排骨架健康，**债务集中在契约不一致与半完成抽象**，而非缺少平台格式。

最高 ROI：

1. **锁死配置/路径/平台命名契约**（测试 + 单源）  
2. **收紧安全与默认权限**  
3. **删掉或接上死参数/死代码/双实现**  
4. **CI 质量门禁**

---

## 14. 附录：关键路径索引

```
unifypy/__main__.py
unifypy/cli/argument_parser.py
unifypy/core/engine.py
unifypy/core/event_bus.py
unifypy/core/config.py
unifypy/core/context.py
unifypy/core/platforms.py
unifypy/core/environment.py
unifypy/core/plugin.py
unifypy/plugins/config_plugin.py
unifypy/plugins/prepare_plugin.py
unifypy/plugins/environment_plugin.py
unifypy/plugins/pyinstaller_plugin.py
unifypy/plugins/packaging_plugin.py
unifypy/plugins/dry_run_plugin.py
unifypy/plugins/external_plugins_loader.py
unifypy/plugins/summary_plugin.py
unifypy/plugins/rollback_plugin.py
unifypy/plugins/auto_rollback_plugin.py
unifypy/pyinstaller/config_builder.py
unifypy/utils/tool_manager.py
unifypy/utils/command_runner.py
unifypy/utils/cache_manager.py
unifypy/utils/parallel_builder.py
unifypy/platforms/base.py
unifypy/platforms/registry.py
unifypy/platforms/linux/rpm_packager.py
unifypy/platforms/linux/deb_packager.py
unifypy/platforms/windows/inno_setup.py
unifypy/platforms/macos/post_processor.py
.github/workflows/publish.yml
scripts/release/bump_version.py
pyproject.toml
MANIFEST.in
build.json
.trellis/tasks/
```

---

*只读审计产出。2026-07-25：补充入口全链路、配置契约、冗余清单与 EnvironmentManager/entitlements/CLI 等问题。落地时建议按 Trellis 任务拆分验收。*
