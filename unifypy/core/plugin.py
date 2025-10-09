#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
插件基类与插件管理：提供统一的注册机制，将处理器绑定到事件总线。
"""

from typing import List, Type

from .event_bus import EventBus


class BasePlugin:
    name: str = "base"
    priority: int = 100

    def __init__(self, context):
        self.context = context

    def register(self, bus: EventBus):
        """子类实现：在此方法中将自身的各事件处理器订阅到总线。"""
        raise NotImplementedError


class PluginManager:
    """插件管理器：加载并注册内置插件（以及后续可扩展的外部插件）。"""

    def __init__(self, context):
        self.context = context

    def load_builtin_plugins(self) -> List[BasePlugin]:
        # 延迟导入避免循环依赖
        from unifypy.plugins.progress_plugin import ProgressPlugin
        from unifypy.plugins.dry_run_plugin import DryRunPlugin
        from unifypy.plugins.config_plugin import ConfigPlugin
        from unifypy.plugins.external_plugins_loader import ExternalPluginsLoaderPlugin
        from unifypy.plugins.environment_plugin import EnvironmentPlugin
        from unifypy.plugins.windows_language_plugin import WindowsLanguagePlugin
        from unifypy.plugins.prepare_plugin import PreparePlugin
        from unifypy.plugins.pyinstaller_plugin import PyInstallerPlugin
        from unifypy.plugins.packaging_plugin import PackagingPlugin
        from unifypy.plugins.summary_plugin import SummaryPlugin
        from unifypy.plugins.cleanup_plugin import CleanupPlugin
        from unifypy.plugins.rollback_plugin import RollbackPlugin
        from unifypy.plugins.auto_rollback_plugin import AutoRollbackPlugin

        plugins: List[BasePlugin] = [
            ProgressPlugin(self.context),
            DryRunPlugin(self.context),
            RollbackPlugin(self.context),
            ExternalPluginsLoaderPlugin(self.context),
            ConfigPlugin(self.context),
            EnvironmentPlugin(self.context),
            WindowsLanguagePlugin(self.context),
            AutoRollbackPlugin(self.context),
            PreparePlugin(self.context),
            PyInstallerPlugin(self.context),
            PackagingPlugin(self.context),
            SummaryPlugin(self.context),
            CleanupPlugin(self.context),
        ]
        return plugins

    def register_plugins(self, bus: EventBus, plugins: List[BasePlugin]):
        for p in plugins:
            p.register(bus)
