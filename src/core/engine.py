#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
构建引擎：协调事件顺序，驱动插件化生命周期。
"""

from .event_bus import EventBus
from .events import (
    ON_START,
    HANDLE_ROLLBACK_COMMANDS,
    LOAD_CONFIG,
    ENVIRONMENT_CHECK,
    PREPARE,
    BUILD_EXECUTABLE,
    GENERATE_INSTALLERS,
    ON_SUCCESS,
    ON_EXIT,
    ON_ERROR,
)


class Engine:
    def __init__(self, context, plugin_manager):
        self.context = context
        self.plugin_manager = plugin_manager
        self.bus = EventBus()

    def setup(self):
        plugins = self.plugin_manager.load_builtin_plugins()
        self.plugin_manager.register_plugins(self.bus, plugins)

    def run(self) -> int:
        ctx = self.context
        try:
            # 生命周期事件顺序
            self.bus.emit(ON_START, ctx)
            if ctx.errors:
                raise ctx.errors[-1][1]

            # 回滚命令处理（列出/执行后退出）
            self.bus.emit(HANDLE_ROLLBACK_COMMANDS, ctx)
            if ctx.should_exit:
                self.bus.emit(ON_EXIT, ctx)
                return ctx.exit_code

            self.bus.emit(LOAD_CONFIG, ctx)
            if ctx.errors:
                raise ctx.errors[-1][1]
            self.bus.emit(ENVIRONMENT_CHECK, ctx)
            if ctx.errors:
                raise ctx.errors[-1][1]
            self.bus.emit(PREPARE, ctx)
            if ctx.errors:
                raise ctx.errors[-1][1]

            # 可执行文件构建
            self.bus.emit(BUILD_EXECUTABLE, ctx)
            if ctx.errors:
                raise ctx.errors[-1][1]

            # 安装包生成
            self.bus.emit(GENERATE_INSTALLERS, ctx)
            if ctx.errors:
                raise ctx.errors[-1][1]

            # 成功收尾
            self.bus.emit(ON_SUCCESS, ctx)
            self.bus.emit(ON_EXIT, ctx)
            return 0

        except KeyboardInterrupt:
            # 友好处理用户中断
            try:
                if getattr(ctx, "progress", None):
                    ctx.progress.on_error(Exception("用户中断"), "构建过程")
            finally:
                try:
                    # 触发错误处理钩子以便自动回滚与清理
                    try:
                        self.bus.emit(ON_ERROR, ctx)
                    except Exception:
                        pass
                    self.bus.emit(ON_EXIT, ctx)
                finally:
                    return 1
        except Exception as e:
            # 收敛异常通知
            ctx.errors.append(("engine", e))
            try:
                self.bus.emit(ON_ERROR, ctx)
                self.bus.emit(ON_EXIT, ctx)
            finally:
                return 1
