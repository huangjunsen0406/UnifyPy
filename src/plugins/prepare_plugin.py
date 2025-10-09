#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path

from src.core.plugin import BasePlugin
from src.core.event_bus import EventBus
from src.core.events import PREPARE
from src.utils.file_ops import FileOperations


class PreparePlugin(BasePlugin):
    name = "prepare"
    priority = 40

    def register(self, bus: EventBus):
        bus.subscribe(PREPARE, self.prepare, priority=self.priority)

    def prepare(self, ctx):
        stage = "环境准备"
        if ctx.progress:
            ctx.progress.start_stage(stage, "创建构建目录和临时文件")

        ctx.file_ops = ctx.file_ops or FileOperations()

        # 创建临时目录
        temp_dir = ctx.file_ops.create_temp_dir("unifypy_build_")
        ctx.temp_dir = Path(temp_dir)
        if ctx.progress:
            ctx.progress.update_stage(stage, 20, f"创建临时目录: {ctx.temp_dir}", absolute=True)

        # 创建输出目录
        ctx.file_ops.ensure_dir(str(ctx.dist_dir))
        ctx.file_ops.ensure_dir(str(ctx.installer_dir))
        if ctx.progress:
            ctx.progress.update_stage(stage, 40, "创建输出目录", absolute=True)

        # 清理旧文件（按需）
        if getattr(ctx.args, "clean", False):
            if ctx.progress:
                ctx.progress.update_stage(stage, 60, "清理旧的构建文件", absolute=True)
            ctx.file_ops.remove_dir(str(ctx.dist_dir))
            ctx.file_ops.remove_dir(str(ctx.installer_dir))
            ctx.file_ops.ensure_dir(str(ctx.dist_dir))
            ctx.file_ops.ensure_dir(str(ctx.installer_dir))

        # 预生成多平台配置（按需）
        try:
            if ctx.cache_manager and ctx.cache_manager.should_pre_generate_all_configs(ctx.config.merged_config):
                if ctx.progress:
                    ctx.progress.update_stage(stage, 45, "预生成多平台配置", absolute=True)
                # 仅在 verbose 下输出详细日志
                def cb(msg, level='info'):
                    if getattr(ctx.args, "verbose", False) and ctx.progress:
                        ctx.progress.info(msg)
                results = ctx.cache_manager.pre_generate_all_platform_configs(
                    ctx.config.merged_config,
                    ctx.config.config_path if hasattr(ctx.config, 'config_path') else None,
                    progress_callback=cb,
                )
                # 简要摘要
                success_count = len([k for k, v in results.items() if v is True])
                total_count = len([k for k, v in results.items() if v != "skipped"]) or 0
                if success_count > 0 and ctx.progress:
                    if not getattr(ctx.args, "verbose", False):
                        ctx.progress.info(f"✅ 已预生成 {success_count}/{total_count} 个平台配置")
                    else:
                        ctx.progress.info(f"✅ 预生成 {success_count}/{total_count} 个平台配置完成")
            else:
                if ctx.progress:
                    ctx.progress.update_stage(stage, 45, "使用缓存配置", absolute=True)
                    if getattr(ctx.args, "verbose", False):
                        ctx.progress.info("📋 使用现有缓存配置")
        except Exception as e:
            if ctx.progress:
                ctx.progress.warning(f"配置预生成失败: {e}")

        # 预处理图标（如无效则移除，避免PyInstaller报错）
        icon_path = ctx.config.get("icon")
        if icon_path:
            icon_full = ctx.config.resolve_path(icon_path)
            if not icon_full.exists():
                ctx.config.merged_config.pop("icon", None)
                if "pyinstaller" in ctx.config.merged_config:
                    ctx.config.merged_config["pyinstaller"].pop("icon", None)

        if ctx.progress:
            ctx.progress.update_stage(stage, 80, "准备资源文件", absolute=True)
            ctx.progress.complete_stage(stage)
