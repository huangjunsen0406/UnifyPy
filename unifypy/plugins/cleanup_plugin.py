#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unifypy.core.plugin import BasePlugin
from unifypy.core.event_bus import EventBus
from unifypy.core.events import ON_EXIT


class CleanupPlugin(BasePlugin):
    name = "cleanup"
    priority = 995

    def register(self, bus: EventBus):
        bus.subscribe(ON_EXIT, self.on_exit, priority=self.priority)

    def on_exit(self, ctx):
        # 清理临时目录
        try:
            if getattr(ctx, "temp_dir", None) and ctx.file_ops:
                ctx.file_ops.cleanup_temp_dir(str(ctx.temp_dir))
        except Exception:
            pass
