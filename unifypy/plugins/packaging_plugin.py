#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import List
from pathlib import Path

from unifypy.core.plugin import BasePlugin
from unifypy.core.event_bus import EventBus
from unifypy.core.events import GENERATE_INSTALLERS
from unifypy.utils.parallel_builder import ParallelBuilder


class PackagingPlugin(BasePlugin):
    name = "packaging"
    priority = 60

    def register(self, bus: EventBus):
        bus.subscribe(GENERATE_INSTALLERS, self.generate_installers, priority=self.priority)

    def generate_installers(self, ctx):
        if getattr(ctx.args, "skip_installer", False):
            return

        stage = "安装包生成"
        if ctx.progress:
            ctx.progress.start_stage(stage, "生成平台特定的安装包")

        platform = ctx.config.current_platform
        requested_formats = self._get_requested_formats(ctx, platform)

        if not requested_formats:
            if ctx.progress:
                ctx.progress.warning(f"未指定 {platform} 平台的输出格式")
                ctx.progress.complete_stage(stage)
            return

        # 源文件路径
        app_name = ctx.config.get("name")
        if ctx.config.get_pyinstaller_config().get("onefile"):
            source_path = ctx.dist_dir / f"{app_name}{ctx.file_ops.get_executable_extension()}"
        else:
            source_path = ctx.dist_dir / app_name

        # 并行或串行
        success_count = 0
        total_formats = len(requested_formats)

        processed_config = ctx.config.preprocess_paths(ctx.config.merged_config)

        if getattr(ctx.args, "parallel", False) and total_formats > 1:
            try:
                with ParallelBuilder(ctx.progress, ctx.args.max_workers) as pb:
                    pb.optimize_pyinstaller_build(ctx.config.get_pyinstaller_config(), str(ctx.project_dir / ctx.config.get("entry")), ctx.project_dir)
                    results = pb.build_multiple_formats(platform, requested_formats, ctx.packager_registry, source_path, ctx.installer_dir, processed_config)
                    success_count = sum(1 for s in results.values() if s)
            except Exception as e:
                ctx.progress.on_error(Exception(f"并行构建失败: {e}"), stage)
                success_count = 0
        else:
            for i, fmt in enumerate(requested_formats):
                format_progress = int(80 * (i + 1) / total_formats)
                if self._build_single_format(ctx, platform, fmt, source_path, processed_config, format_progress):
                    success_count += 1

        if success_count == 0:
            ctx.progress.on_error(Exception("所有格式的安装包生成都失败了"), stage)
        elif success_count < total_formats:
            ctx.progress.warning(f"部分安装包生成失败 ({success_count}/{total_formats} 成功)")

        if ctx.progress:
            ctx.progress.complete_stage(stage)

    def _build_single_format(self, ctx, platform: str, format_type: str, source_path: Path, processed_config: dict, progress_weight: int) -> bool:
        packager_class = ctx.packager_registry.get_packager(platform, format_type)
        if not packager_class:
            ctx.progress.warning(f"未找到 {platform}/{format_type} 格式的打包器")
            return False

        packager = packager_class(ctx.progress, ctx.runner, ctx.tool_manager, processed_config)

        errors = packager.validate_config(format_type)
        if errors:
            ctx.progress.warning(f"{format_type}格式配置验证失败:")
            for err in errors:
                ctx.progress.warning(f"  - {err}")

        app_name = ctx.config.get("name")
        version = ctx.config.get("version")
        output_filename = packager.get_output_filename(format_type, app_name, version)
        output_path = ctx.installer_dir / output_filename

        ctx.progress.update_stage("安装包生成", 0, f"正在生成 {format_type.upper()} 格式安装包...")

        try:
            success = packager.package(format_type, source_path, output_path)
            if success:
                ctx.progress.update_stage("安装包生成", progress_weight)
                ctx.progress.info(f"✅ {format_type.upper()} 安装包已生成: {output_path}")
                return True
            else:
                ctx.progress.warning(f"❌ {format_type.upper()} 安装包生成失败")
                return False
        except Exception as e:
            ctx.progress.on_error(Exception(f"{format_type.upper()} 打包失败: {e}"), "安装包生成")
            return False

    def _get_requested_formats(self, ctx, platform: str) -> List[str]:
        # 优先命令行指定
        if ctx.args.format:
            return [ctx.args.format]

        platform_config = ctx.config.get("platforms", {}).get(platform, {})
        formats = []
        for key in platform_config.keys():
            if ctx.packager_registry.is_format_supported(platform, key):
                formats.append(key)

        if not formats:
            default_formats = {
                "windows": ["exe"],
                "macos": ["dmg"],
                "linux": ["deb"],
            }
            formats = default_formats.get(platform, [])
        return formats
