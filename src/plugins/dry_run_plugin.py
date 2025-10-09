#!/usr/bin/env python
# -*- coding: utf-8 -*-

from src.core.plugin import BasePlugin
from src.core.event_bus import EventBus
from src.core.events import ON_START


class DryRunPlugin(BasePlugin):
    name = "dry_run"
    priority = 12  # 在 Progress(10) 之后、Rollback(15) 之前

    def register(self, bus: EventBus):
        bus.subscribe(ON_START, self.on_start, priority=self.priority)

    def on_start(self, ctx):
        # 仅设置标志，后续阶段自然跳过
        if getattr(ctx.args, "dry_run", False):
            setattr(ctx.args, "skip_exe", True)
            setattr(ctx.args, "skip_installer", True)
            if ctx.progress:
                ctx.progress.info("🔎 Dry-run 模式：仅执行环境检查与准备，跳过构建与打包")

