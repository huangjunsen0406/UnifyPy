#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unifypy.core.plugin import BasePlugin
from unifypy.core.event_bus import EventBus
from unifypy.core.events import ENVIRONMENT_CHECK
from unifypy.core.validators.tool_validator import ToolValidator
from unifypy.utils.tool_manager import ToolManager
from unifypy.core.platforms import normalize_arch, is_supported_arch


class EnvironmentPlugin(BasePlugin):
    name = "environment"
    priority = 30

    def register(self, bus: EventBus):
        bus.subscribe(ENVIRONMENT_CHECK, self.environment_check, priority=self.priority)

    def environment_check(self, ctx):
        stage = "环境检查"
        if ctx.progress:
            ctx.progress.start_stage(stage, "验证项目配置和依赖")

        # 检查项目目录与入口文件
        if not ctx.project_dir.exists():
            raise FileNotFoundError(f"项目目录不存在: {ctx.project_dir}")
        if ctx.progress:
            ctx.progress.update_stage(stage, 10, "检查入口文件", absolute=True)
        entry_file = ctx.config.resolve_path(ctx.config.get("entry"))
        if not entry_file.exists():
            raise FileNotFoundError(f"入口文件不存在: {entry_file}")

        # 工具检测
        ctx.tool_manager = ctx.tool_manager or ToolManager()
        validator = ToolValidator(tool_manager=ctx.tool_manager, progress_manager=ctx.progress)

        # 架构检测（仅支持 x64/arm64）
        try:
            arch = normalize_arch()
            if not is_supported_arch(arch):
                raise ValueError(f"不支持的架构: {arch}（仅支持 x64/arm64）")
        except Exception as e:
            raise RuntimeError(str(e))

        # PyInstaller 可用性
        from unifypy.utils.command_runner import SilentRunner

        ctx.runner = ctx.runner or SilentRunner(ctx.progress)
        if not ctx.runner.check_tool_available("pyinstaller"):
            raise RuntimeError("PyInstaller未安装，请运行: pip install pyinstaller")

        # 平台特定打包器
        if not getattr(ctx.args, "skip_installer", False):
            format_type = getattr(ctx.args, "format", None)
            if format_type:
                # CLI 指定了格式，只检查该格式的工具
                validator.validate_and_raise(
                    platform=ctx.config.current_platform,
                    verbose=True,
                    format_type=format_type,
                    config=ctx.config.merged_config,
                )
            else:
                # 从配置推断要打的格式，逐个检测
                requested_formats = self._get_formats_from_config(ctx)
                for fmt in requested_formats:
                    validator.validate_and_raise(
                        platform=ctx.config.current_platform,
                        verbose=True,
                        format_type=fmt,
                        config=ctx.config.merged_config,
                    )

        # 磁盘空间提示
        if ctx.file_ops and not ctx.file_ops.check_disk_space(str(ctx.project_dir), 500):
            ctx.progress.warning("磁盘空间可能不足（建议至少500MB）")

        if ctx.progress:
            ctx.progress.complete_stage(stage)

    def _get_formats_from_config(self, ctx) -> list:
        """从配置推断要打的格式列表."""
        platform = ctx.config.current_platform
        platform_config = ctx.config.get("platforms", {}).get(platform, {})

        # 优先使用显式 formats 列表
        if "formats" in platform_config:
            explicit = platform_config["formats"]
            if isinstance(explicit, list) and explicit:
                return explicit

        # fallback: 遍历 key 检测
        formats = []
        for key in platform_config.keys():
            if ctx.packager_registry and ctx.packager_registry.is_format_supported(platform, key):
                formats.append(key)

        if not formats:
            default_formats = {"windows": ["exe"], "macos": ["dmg"], "linux": ["deb"]}
            formats = default_formats.get(platform, [])

        return formats
