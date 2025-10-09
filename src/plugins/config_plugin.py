#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path

from src.core.plugin import BasePlugin
from src.core.event_bus import EventBus
from src.core.events import LOAD_CONFIG
from src.core.context import BuildContext
from src.core.config import ConfigManager
from src.utils.file_ops import FileOperations
from src.utils.cache_manager import CacheManager
from src.platforms.registry import PackagerRegistry
from src.core.environment import EnvironmentManager


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

        # 加载配置
        try:
            ctx.config = ConfigManager(config_path=ctx.args.config, args=vars(ctx.args))
        except Exception as e:
            ctx.errors.append(("load_config", e))
            raise

        # 初始化缓存管理器
        ctx.cache_manager = CacheManager(str(ctx.project_dir))

        # 创建常用目录
        ctx.file_ops.ensure_dir(str(ctx.dist_dir))
        ctx.file_ops.ensure_dir(str(ctx.installer_dir))
