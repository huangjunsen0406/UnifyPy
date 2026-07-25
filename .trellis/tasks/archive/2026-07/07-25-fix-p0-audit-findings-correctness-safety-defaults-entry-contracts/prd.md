# Fix P0 audit findings (Approach C: aggressive safety)

## Goal

按 `AUDIT_REPORT.md` 落地 **Approach C**：正确性热修 + 安全默认收紧 + 入口契约 + **macOS entitlements 默认 production** + **下载强制 SHA256**，并补最小单元测试。

## Decision (ADR-lite)

**Context**: 用户在 A/B/C 中选择 C（激进安全）。  
**Decision**: 本任务实现 C 全量范围。  
**Consequences**:
- 自动 sudo / 静默装工具默认关闭，需 `--allow-auto-install`
- 下载 appimagetool 等必须通过内置 SHA256；未知版本拒绝执行
- macOS 默认不再带 development entitlements；调试需 `--development`
- 可能打断依赖「静默装工具 / 默认开发权限」的旧脚本

## Requirements

### 正确性

1. **R1** RPM：`run_command(..., env=env)` 传入构建 env  
2. **R2** macOS：`_verify_output` 对非 onefile 校验 `dist/{name}.app`（及 display_name 变体若已存在）  
3. **R3** `BasePackager` 使用真实 `project_dir` 构造 `EnvironmentManager`；packaging 传入 project_dir  
4. **R4** `--config` 相对路径相对 `project_dir` 解析  
5. **R5** 版本单一来源：`__version__` 与 pyproject 对齐；`cache_manager` 读真实版本；`bump_version.py` 同步 `__init__.py`

### 安全默认

6. **R6** `SilentRunner.run_command` 默认 `shell=False`  
7. **R7** 自动安装（sudo apt/dnf、静默 Inno、下载 appimagetool）**仅当** `allow_auto_install=True`（CLI `--allow-auto-install`）；否则只打印安装指引  
8. **R8** `_download_file` 支持/要求 expected_sha256；appimagetool 使用钉死版本 URL + 内置 hash 表；校验失败删除文件并报错；zip extract 防 Zip Slip  
9. **R9** Inno 静默安装同样受 R7 门控；无 hash 的官方安装包在允许自动安装时仍下载但应警告（或仅提示手动安装——优先：**Inno 默认只提示手动安装+链接，不自动下载执行**，比带弱校验更安全）

### 入口契约

10. **R10** CLI：help/epilog 用 `unifypy`；`--format` 含 appimage；`--version` 打印工具版本；`--quiet` 降低 progress 输出；`--allow-auto-install`  
11. **R11** macOS entitlements：**默认 production**（`development=False`，除非 `--development` 或显式 debug）；去掉「默认 development」逻辑  

### 测试

12. **R12** `tests/`：config 路径解析、shell 默认、rpm env 调用、verify_output 路径选择、entitlements development 标志、download sha256 失败、版本读取；可用 pytest + mock

## Acceptance Criteria

- [ ] RPM runner 收到 env（单测或代码审查+mock）  
- [ ] macOS onedir 校验 `.app` 存在即通过  
- [ ] Packager.env_manager.project_dir == 用户项目根  
- [ ] 任意 cwd 下 `ConfigManager`/`--config relative.json` 相对 project_dir 可加载  
- [ ] `__version__` == pyproject version；cache hash 含该版本  
- [ ] `shell` 默认 False  
- [ ] 无 `--allow-auto-install` 时不调用 sudo / 不静默装 Inno / 不擅自下载执行 appimagetool  
- [ ] appimagetool 下载校验 SHA256；错误 hash 拒绝  
- [ ] zip 解压拒绝 `../` 逃逸路径  
- [ ] 默认 entitlements 为 production；`--development` 才加开发权限  
- [ ] `pytest` 本地通过  
- [ ] `--help` 显示 unifypy 示例；`--version` 可用  

## Definition of Done

- 测试新增并通过  
- README 简短说明行为变更（auto-install、development、下载校验）——可最小补丁  
- 不引入交叉编译  

## Out of Scope

- 完整多 OS CI 打包矩阵  
- CacheManager 双实现完全合并  
- JSON Schema、巨石拆分  
- Trusted Publisher / create-release 替换（可选顺手）  
- 业务配置 py-xiaozhi.json  

## Technical Approach

1. CLI 参数与 Progress quiet  
2. Config 路径 resolve + version helpers  
3. base packager project_dir + packaging 传参  
4. pyinstaller verify + post_processor development 默认  
5. command_runner shell 默认  
6. tool_manager：allow_auto_install 门控、sha256、safe extract  
7. tool_validator 传递 allow flag  
8. tests  

## Technical Notes

- 参考：`AUDIT_REPORT.md`  
- appimagetool：优先钉 `continuous` 或固定 release；hash 可对当前 continuous 在实现时用脚本计算并写入常量，或使用 GitHub release 固定 tag  
- 若 continuous 哈希常变：**钉死具体 release asset URL + hash**（实现时选 stable 策略）  
- 文件：见 implement 范围  

## Research References

- 本地审计：`AUDIT_REPORT.md`（无需外部调研即可落地）
