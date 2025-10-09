#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unifypy.core.plugin import BasePlugin
from unifypy.core.event_bus import EventBus
from unifypy.core.events import HANDLE_ROLLBACK_COMMANDS
from unifypy.utils.rollback import RollbackManager


class RollbackPlugin(BasePlugin):
    name = "rollback"
    priority = 15

    def register(self, bus: EventBus):
        bus.subscribe(HANDLE_ROLLBACK_COMMANDS, self.handle_commands, priority=self.priority)

    def handle_commands(self, ctx):
        # 列出回滚会话
        if getattr(ctx.args, "list_rollback", False):
            rb = RollbackManager(ctx.project_dir, ctx.progress)
            sessions = rb.list_rollback_sessions()
            if not sessions:
                print("没有可用的回滚会话")
                ctx.exit_code = 0
                ctx.should_exit = True
                return
            print("可用的回滚会话:")
            print("-" * 60)
            for session_id in sessions:
                info = rb.get_session_info(session_id)
                if info:
                    import datetime
                    start_time = datetime.datetime.fromtimestamp(info["start_time"]) if info.get("start_time") else None
                    print(f"会话ID: {session_id}")
                    if start_time:
                        print(f"  时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"  操作数: {info.get('operation_count', 0)}")
                    print(f"  回滚命令: python main.py . --rollback {session_id}")
                    print()
            ctx.exit_code = 0
            ctx.should_exit = True
            return

        # 执行回滚
        if getattr(ctx.args, "rollback", None):
            session_id = ctx.args.rollback
            rb = RollbackManager(ctx.project_dir, ctx.progress)
            if not rb.load_operations(session_id):
                print(f"错误: 会话 {session_id} 不存在或无法加载")
                ctx.exit_code = 1
                ctx.should_exit = True
                return
            print(f"正在回滚会话: {session_id}")
            success = rb.rollback()
            if success:
                print("✅ 回滚成功完成")
                rb.cleanup()
                ctx.exit_code = 0
            else:
                print("❌ 回滚过程中发生错误")
                ctx.exit_code = 1
            ctx.should_exit = True
