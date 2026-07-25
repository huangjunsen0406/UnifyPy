#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Optional

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

        # 可执行文件 / 应用包
        if not getattr(ctx.args, "skip_exe", False):
            exe_path = self.resolve_executable_path(ctx)
            if exe_path is not None and exe_path.exists():
                output_info["可执行文件"] = str(exe_path)

        # 安装包
        if not getattr(ctx.args, "skip_installer", False) and ctx.installer_dir.exists():
            installer_files = [str(p) for p in ctx.installer_dir.iterdir() if p.is_file()]
            if installer_files:
                output_info["安装包"] = installer_files[0] if len(installer_files) == 1 else installer_files

        if ctx.progress:
            ctx.progress.show_success(output_info)

    @staticmethod
    def resolve_executable_path(ctx) -> Optional[Path]:
        """Resolve the primary build output path for the success summary.

        On macOS prefer real ``.app`` bundles (display_name then name) so the
        summary does not report a tiny leftover ``dist/<name>`` directory.
        """
        app_name = ctx.config.get("name")
        if not app_name:
            return None

        dist_dir = ctx.dist_dir
        onefile = bool(ctx.config.get_pyinstaller_config().get("onefile"))
        platform = getattr(ctx.config, "current_platform", None)
        ext = ""
        if hasattr(ctx, "file_ops") and ctx.file_ops is not None:
            ext = ctx.file_ops.get_executable_extension() or ""

        if onefile:
            return dist_dir / f"{app_name}{ext}"

        # macOS BUNDLE / post-process may produce display_name.app or name.app
        if platform == "macos":
            candidates = []
            display_name = ctx.config.get("display_name")
            if display_name:
                candidates.append(dist_dir / f"{display_name}.app")
            candidates.append(dist_dir / f"{app_name}.app")
            for path in candidates:
                if path.exists():
                    return path
            # Fall back to previous onedir layout if no .app is present
            onedir = dist_dir / app_name
            if onedir.exists():
                return onedir
            return candidates[0]

        return dist_dir / app_name
