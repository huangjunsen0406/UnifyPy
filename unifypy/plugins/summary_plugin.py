#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unifypy.core.plugin import BasePlugin
from unifypy.core.event_bus import EventBus
from unifypy.core.events import ON_SUCCESS


class SummaryPlugin(BasePlugin):
    name = "summary"
    priority = 90

    def register(self, bus: EventBus):
        bus.subscribe(ON_SUCCESS, self.on_success, priority=self.priority)

    def on_success(self, ctx):
        output_info = {}
        app_name = ctx.config.get("name")

        # 可执行文件
        if not getattr(ctx.args, "skip_exe", False):
            if ctx.config.get_pyinstaller_config().get("onefile"):
                exe_path = ctx.dist_dir / f"{app_name}{ctx.file_ops.get_executable_extension()}"
            else:
                exe_path = ctx.dist_dir / app_name
            if exe_path.exists():
                output_info["可执行文件"] = str(exe_path)

        # 安装包
        if not getattr(ctx.args, "skip_installer", False) and ctx.installer_dir.exists():
            installer_files = [str(p) for p in ctx.installer_dir.iterdir() if p.is_file()]
            if installer_files:
                output_info["安装包"] = installer_files[0] if len(installer_files) == 1 else installer_files

        if ctx.progress:
            ctx.progress.show_success(output_info)
