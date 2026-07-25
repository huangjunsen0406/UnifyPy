#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unifypy.core.plugin import BasePlugin
from unifypy.core.event_bus import EventBus
from unifypy.core.events import LOAD_CONFIG
from unifypy.core.context import BuildContext
from unifypy.core.config import ConfigManager
from unifypy.utils.file_ops import FileOperations
from unifypy.utils.cache_manager import CacheManager
from unifypy.platforms.registry import PackagerRegistry
from unifypy.core.environment import EnvironmentManager


class ConfigPlugin(BasePlugin):
    name = "config"
    priority = 20

    def register(self, bus: EventBus):
        bus.subscribe(LOAD_CONFIG, self.load_config, priority=self.priority)

    def load_config(self, ctx: BuildContext):
        # 准备基础组件
        ctx.file_ops = ctx.file_ops or FileOperations()
        ctx.packager_registry = ctx.packager_registry or PackagerRegistry()
        ctx.env_manager = ctx.env_manager or EnvironmentManager(str(ctx.project_dir))

        # 加载配置（相对路径相对 project_dir 解析，而非 cwd）
        try:
            config_path = self._resolve_config_path(
                getattr(ctx.args, "config", None), ctx.project_dir
            )
            ctx.config = ConfigManager(config_path=config_path, args=vars(ctx.args))
        except Exception as e:
            ctx.errors.append(("load_config", e))
            raise

        # 初始化缓存管理器
        ctx.cache_manager = CacheManager(str(ctx.project_dir))

    @staticmethod
    def _resolve_config_path(config_path, project_dir):
        """Resolve --config relative to project_dir when not absolute."""
        if not config_path:
            return config_path
        from pathlib import Path

        path = Path(config_path)
        if path.is_absolute():
            return str(path)
        return str((Path(project_dir) / path).resolve())
