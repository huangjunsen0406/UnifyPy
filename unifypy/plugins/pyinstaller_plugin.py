#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import os

from unifypy.core.plugin import BasePlugin
from unifypy.core.event_bus import EventBus
from unifypy.core.events import BUILD_EXECUTABLE
from unifypy.pyinstaller.config_builder import PyInstallerConfigBuilder
from unifypy.utils.progress_callback_factory import ProgressCallbackFactory
from unifypy.utils.info_plist_updater import InfoPlistUpdater
from unifypy.utils.macos_codesign import MacOSCodeSigner
from unifypy.platforms.macos.post_processor import MacOSPostProcessor


class PyInstallerPlugin(BasePlugin):
    name = "pyinstaller"
    priority = 50

    def register(self, bus: EventBus):
        bus.subscribe(BUILD_EXECUTABLE, self.build_executable, priority=self.priority)

    def build_executable(self, ctx):
        if getattr(ctx.args, "skip_exe", False):
            return

        stage = "PyInstaller打包"
        if ctx.progress:
            ctx.progress.start_stage(stage, "使用PyInstaller生成可执行文件")

        # 进度回调
        cb = ProgressCallbackFactory.create_callback(ctx.progress, verbose=getattr(ctx.args, "verbose", False))

        # 构建器与 macOS 处理器
        builder = PyInstallerConfigBuilder(current_platform=ctx.config.current_platform, verbose=getattr(ctx.args, "verbose", False), progress_callback=cb)
        info_plist_updater = InfoPlistUpdater(verbose=getattr(ctx.args, "verbose", False))
        mac_codesigner = MacOSCodeSigner(verbose=getattr(ctx.args, "verbose", False))
        mac_processor = MacOSPostProcessor(info_plist_updater, mac_codesigner, builder, verbose=getattr(ctx.args, "verbose", False))

        # macOS: 预处理 entitlements 并合并 pyinstaller 配置
        if mac_processor.is_macos():
            if ctx.progress:
                ctx.progress.update_stage(stage, 5, "检查 macOS 权限配置")
            updated = mac_processor.prepare_entitlements_config(ctx.config, ctx.project_dir, ctx.args)
            if updated and updated != ctx.config.raw_config:
                if "pyinstaller" in updated:
                    if "pyinstaller" not in ctx.config.merged_config:
                        ctx.config.merged_config["pyinstaller"] = {}
                    ctx.config.merged_config["pyinstaller"].update(updated["pyinstaller"])

        # 生成 spec 文件并执行
        py_cfg = ctx.config.get_pyinstaller_config()
        entry = str((ctx.project_dir / ctx.config.get("entry")).resolve())

        # 构建完整的配置字典（包含 platforms.macos 配置）
        full_config = {
            "name": ctx.config.get("name"),
            "version": ctx.config.get("version"),
            "icon": ctx.config.get("icon"),
            "publisher": ctx.config.get("publisher", ""),
        }
        full_config.update(py_cfg)

        # 添加 platforms 配置（用于 BUNDLE 的 info_plist）
        if "platforms" in ctx.config.raw_config:
            full_config["platforms"] = ctx.config.raw_config["platforms"]

        # spec 文件缓存：检查配置是否变化
        app_name = ctx.config.get("name")
        spec_file = ctx.project_dir / f"{app_name}.spec"

        should_regenerate_spec = True
        if spec_file.exists() and hasattr(ctx, 'cache_manager'):
            # 检查配置是否变化
            current_hash = ctx.cache_manager.calculate_config_hash(ctx.config.raw_config, ctx.config.current_platform)
            stored_hash = ctx.cache_manager.load_cached_hash(ctx.config.current_platform)

            if getattr(ctx.args, 'verbose', False):
                cb(f"🔍 spec 缓存检查: current={current_hash[:8] if current_hash else None}, stored={stored_hash[:8] if stored_hash else None}", 'info')

            if current_hash == stored_hash and stored_hash is not None:
                should_regenerate_spec = False
                cb(f"✅ 配置未变化，使用现有 spec 文件: {spec_file}", 'success')

        if should_regenerate_spec:
            # 生成 spec 文件
            if ctx.progress:
                ctx.progress.update_stage(stage, 10, "生成 spec 文件", absolute=True)

            spec_content = builder.build_spec_file_content(full_config, entry)

            with open(spec_file, 'w', encoding='utf-8') as f:
                f.write(spec_content)

            cb(f"✅ spec 文件已生成: {spec_file}", 'success')

            # 更新配置 hash
            if hasattr(ctx, 'cache_manager'):
                new_hash = ctx.cache_manager.calculate_config_hash(ctx.config.raw_config, ctx.config.current_platform)
                ctx.cache_manager.save_config_hash(new_hash, ctx.config.current_platform)

        # 使用 spec 文件打包
        command = ["pyinstaller", str(spec_file)]

        # 在项目根目录执行命令（使用 cwd 参数，避免全局 chdir）
        if ctx.progress:
            ctx.progress.update_stage(stage, 20, "执行 PyInstaller", absolute=True)
        success = ctx.runner.run_command(
            command,
            stage=stage,
            step_description="运行 PyInstaller",
            step_weight=60,
            capture_output=True,
            shell=False,
            cwd=str(ctx.project_dir),
        )

        if not success:
            raise RuntimeError("PyInstaller打包失败")

        if ctx.progress:
            ctx.progress.update_stage(stage, 90, "验证输出文件", absolute=True)

        # 验证输出
        self._verify_output(ctx)

        # macOS 后处理
        if mac_processor.is_macos():
            app_name = ctx.config.get("name")
            mac_processor.process_built_app(app_name, ctx.dist_dir, ctx.config, ctx.project_dir)

        if ctx.progress:
            ctx.progress.complete_stage(stage)

    def _verify_output(self, ctx):
        app_name = ctx.config.get("name")
        onefile = ctx.config.get_pyinstaller_config().get("onefile")
        if onefile:
            exe_path = ctx.dist_dir / f"{app_name}{ctx.file_ops.get_executable_extension()}"
        else:
            exe_path = ctx.dist_dir / app_name / f"{app_name}{ctx.file_ops.get_executable_extension()}"
        if not exe_path.exists():
            raise RuntimeError(f"PyInstaller输出文件不存在: {exe_path}")
