#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib
from typing import List

from src.core.plugin import BasePlugin
from src.core.event_bus import EventBus
from src.core.events import LOAD_CONFIG


class ExternalPluginsLoaderPlugin(BasePlugin):
    name = "external_plugins_loader"
    priority = 22  # 在 config(20) 之后、env(30) 之前

    def register(self, bus: EventBus):
        self._bus = bus
        bus.subscribe(LOAD_CONFIG, self.load_external_plugins, priority=self.priority)

    def load_external_plugins(self, ctx):
        # 支持在配置中指定：
        # plugins: ["package.module:ClassName", "another.module:Plugin"]
        plugins: List[str] = []
        try:
            plugins = ctx.config.merged_config.get("plugins", []) or []
        except Exception:
            return

        for ref in plugins:
            try:
                module_name, class_name = ref.split(":", 1)
                mod = importlib.import_module(module_name)
                cls = getattr(mod, class_name)
                # 简单校验是否像插件
                instance = cls(ctx)
                if hasattr(instance, "register"):
                    instance.register(self._bus)
                    if ctx.progress:
                        ctx.progress.info(f"🔌 外部插件已加载: {ref}")
            except Exception as e:
                if ctx.progress:
                    ctx.progress.warning(f"加载外部插件失败 {ref}: {e}")
