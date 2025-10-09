#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unifypy.core.plugin import BasePlugin
from unifypy.core.event_bus import EventBus
from unifypy.core.events import ON_START, ON_EXIT, ON_ERROR
from unifypy.utils.progress import ProgressManager


class ProgressPlugin(BasePlugin):
    name = "progress"
    priority = 10

    def register(self, bus: EventBus):
        bus.subscribe(ON_START, self.on_start, priority=self.priority)
        bus.subscribe(ON_EXIT, self.on_exit, priority=999)
        bus.subscribe(ON_ERROR, self.on_error, priority=5)

    def on_start(self, ctx):
        ctx.progress = ProgressManager(verbose=getattr(ctx.args, "verbose", False))
        ctx.progress.start()

    def on_exit(self, ctx):
        if ctx.progress:
            ctx.progress.stop()

    def on_error(self, ctx):
        # 将已收集的错误打印出来（如果有）
        if not ctx.progress:
            return
        for event, err in ctx.errors:
            ctx.progress.on_error(err, f"{event}")
