# Fix config merge and platform tool detection

## Goal

修复 UnifyPy 配置合并和平台工具检测的问题，确保：
1. PyInstaller 配置在各平台正确合并，CLI 参数优先级最高
2. 平台打包工具统一检测，能自动安装的自动装，需手动安装的给出提示
3. Linux 桌面快捷方式能正常启动应用

## Requirements

### R1: 配置合并修复

- **CLI 优先级修复**：`get_pyinstaller_config()` 返回的结果中，CLI 传入的参数（如 `--onefile`, `--windowed`）优先级最高，不被配置文件覆盖
- **去除冗余合并**：`get_pyinstaller_config()` 不再重复合并平台 pyinstaller（`_merge_all_configs` 已经做过）
- **顶层不污染**：`_merge_all_configs()` 合并平台配置时，不把安装器配置（`deb`/`rpm`/`appimage`/`inno_setup`/`dmg`/`formats`）提升到 `merged_config` 顶层。只合并与全局相关的键（`pyinstaller`、`icon`、`name` 等通用属性）
- **保持现有正确行为**：平台 pyinstaller 只覆盖它声明的键，未声明的继承全局

### R2: 格式检测逻辑

- `_get_requested_formats()` 应优先读取 `platforms.{platform}.formats` 列表（如果存在）
- 如果没有 `formats` 字段，再 fallback 到当前的 key 遍历逻辑

### R3: 工具检测与自动安装

- 补充 `appimagetool` 到 `ToolManager.platform_tools["linux"]`
- 环境检查阶段根据实际要打的格式检测工具（从配置推断，不是只看 `--format` CLI 参数）
- `ToolManager._check_inno_setup()` 也检查用户配置中的 `inno_setup_path`
- 可自动安装的工具提供自动安装命令提示
- 需要 GUI 安装的工具（Inno Setup）给出下载链接和步骤

### R4: Linux 桌面启动修复

- DEB/RPM 的 `.desktop` 文件添加 `Path=/opt/{package_name}`
- 启动脚本设置 `LD_LIBRARY_PATH` 指向 `_internal` 目录（PyInstaller onedir 模式的依赖目录）

## Acceptance Criteria

- [ ] `unifypy . --config build.json --onefile` 实际产出单文件（CLI 不被覆盖）
- [ ] Windows 平台 `platforms.windows.pyinstaller.contents_directory` 正确继承到最终配置
- [ ] `merged_config` 顶层不出现 `deb`/`rpm`/`appimage`/`formats` 等安装器键
- [ ] Linux 配置中 `formats: ["rpm", "appimage", "deb"]` 能控制打包哪些格式
- [ ] 配置了 appimage 时环境检查能检测 appimagetool
- [ ] DEB 包安装后桌面图标能启动应用

## Definition of Done

- 修改的模块 lint 通过
- 现有三平台打包流程不回退
- 有单元测试覆盖配置合并优先级

## Technical Approach

### 修复 `config.py`

1. `_merge_all_configs()`: 合并平台配置时过滤掉安装器键
   ```python
   INSTALLER_KEYS = {"deb", "rpm", "appimage", "inno_setup", "dmg", "create_dmg", "formats", "zip"}
   platform_general = {k: v for k, v in platform_config.items() if k not in INSTALLER_KEYS}
   merged = self._deep_merge(merged, platform_general)
   ```

2. `get_pyinstaller_config()`: 简化为正确的优先级链
   ```python
   # 基础: 全局 pyinstaller section
   config = self.merged_config.get("pyinstaller", {}).copy()
   # 覆盖: 平台 pyinstaller（_merge_all_configs 已合并，但为明确性保留）
   # 去除: 不再重复合并
   # 最终覆盖: CLI 参数最高优先级
   cli_keys = ["onefile", "windowed", "console", "icon", "name", ...]
   for key in cli_keys:
       if key in self.args and self.args[key] is not None:
           config[key] = self.args[key]
   ```

### 修复 `packaging_plugin.py`

```python
def _get_requested_formats(self, ctx, platform):
    if ctx.args.format:
        return [ctx.args.format]
    platform_config = ctx.config.get("platforms", {}).get(platform, {})
    # 优先使用显式 formats 列表
    if "formats" in platform_config:
        return platform_config["formats"]
    # fallback: 遍历 key 检测
    ...
```

### 修复 `tool_manager.py`

- 注册 appimagetool
- `_check_inno_setup` 增加配置路径检查

### 修复 Linux 打包器

- `deb_packager.py` / `rpm_packager.py`: 启动脚本加 `LD_LIBRARY_PATH`，desktop 文件加 `Path=`

## Out of Scope

- 新增打包格式支持
- 重构插件架构
- 配置文件格式变更
