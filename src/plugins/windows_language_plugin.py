#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path

from src.core.plugin import BasePlugin
from src.core.event_bus import EventBus
from src.core.events import ENVIRONMENT_CHECK


class WindowsLanguagePlugin(BasePlugin):
    name = "windows_language"
    # 在 environment(30) 之后、prepare(40) 之前
    priority = 32

    def register(self, bus: EventBus):
        bus.subscribe(ENVIRONMENT_CHECK, self.ensure_chinese_language, priority=self.priority)

    def ensure_chinese_language(self, ctx):
        try:
            # 仅在 Windows 平台且未跳过安装器时处理
            if ctx.config.current_platform != "windows" or getattr(ctx.args, "skip_installer", False):
                return

            # 检查是否启用中文语言
            win_cfg = ctx.config.get("platforms", {}).get("windows", {}) or {}
            inno_cfg = win_cfg.get("inno_setup", {}) or {}
            langs = inno_cfg.get("languages", []) or []
            enable_cn = any(l in ["chinesesimplified", "chinese"] for l in langs)
            if not enable_cn:
                return

            # 延迟导入避免循环
            from src.platforms.windows.inno_setup import InnoSetupPackager

            # 构建临时 packager 用于复用其检测与生成逻辑
            packager = InnoSetupPackager(
                ctx.progress,
                ctx.runner,
                ctx.tool_manager,
                ctx.config.merged_config,
                getattr(ctx.config, "config_path", None) or "build.json",
            )

            # 定位 Inno Setup 编译器并推导 Languages 目录
            iscc = packager._find_inno_setup_compiler()
            if not iscc:
                # 工具不可用时不报错，只提示（环境插件已做校验）
                if ctx.progress:
                    ctx.progress.warning("未找到 Inno Setup，跳过中文语言文件准备")
                return

            lang_dir = os.path.join(os.path.dirname(iscc), "Languages")
            os.makedirs(lang_dir, exist_ok=True)
            target = os.path.join(lang_dir, "ChineseSimplified.isl")

            # 若项目自带中文语言文件，则复制到 Languages 目录（确保缓存 ISS 可用）
            proj_cn = getattr(packager, "_project_chinese_file", None)
            if proj_cn and os.path.exists(proj_cn):
                try:
                    if not os.path.exists(target):
                        from shutil import copy2
                        copy2(proj_cn, target)
                        if ctx.progress:
                            ctx.progress.info(f"✅ 已复制项目中文语言文件到: {target}")
                    else:
                        if ctx.progress:
                            ctx.progress.info("🔁 语言文件已存在，跳过复制")
                    return
                except Exception as e:
                    if ctx.progress:
                        ctx.progress.warning(f"复制中文语言文件失败: {e}")

            # 否则：确保 Languages 目录内存在中文语言文件（模板优先）
            if not os.path.exists(target):
                ok = packager._create_basic_chinese_language_file(target)
                if ok and ctx.progress:
                    ctx.progress.info(f"✅ 已准备中文语言文件: {target}")
                elif not ok and ctx.progress:
                    ctx.progress.warning("⚠️ 无法准备中文语言文件，将仅支持英文界面")

        except Exception as e:
            if ctx.progress:
                ctx.progress.warning(f"Windows 中文语言预设失败: {e}")
