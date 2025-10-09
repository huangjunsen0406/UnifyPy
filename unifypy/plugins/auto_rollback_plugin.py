#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path

from unifypy.core.plugin import BasePlugin
from unifypy.core.event_bus import EventBus
from unifypy.core.events import ON_START, PREPARE, ON_ERROR, ON_SUCCESS
from unifypy.utils.rollback import RollbackManager
from unifypy.utils.file_ops import FileOperations


class _RollbackFileOps(FileOperations):
    """包装 FileOperations，使用 RollbackManager 进行安全操作跟踪。"""

    def __init__(self, base_ops: FileOperations, rb: RollbackManager, excluded_roots=None, ignore_patterns=None):
        super().__init__()
        self._base = base_ops
        self._rb = rb
        self._excluded_roots = [Path(p).resolve() for p in (excluded_roots or [])]
        self._ignore_patterns = ignore_patterns or ["__pycache__", ".DS_Store", ".git", ".gitignore", "*.pyc", "*.pyo", "*.log"]

    def _is_excluded(self, p: Path) -> bool:
        p = p.resolve()
        for root in self._excluded_roots:
            try:
                if root in p.parents or p == root:
                    return True
            except Exception:
                continue
        return False

    def _is_ignored_file(self, p: Path) -> bool:
        name = p.name
        # 简单匹配通配符后缀
        for pat in self._ignore_patterns:
            if pat == name:
                return True
            if pat.startswith("*.") and name.endswith(pat[1:]):
                return True
        return False

    def ensure_dir(self, dir_path: str):
        p = Path(dir_path)
        if self._is_excluded(p):
            return self._base.ensure_dir(dir_path)
        if not p.exists():
            self._rb.safe_create_dir(p)
        else:
            self._base.ensure_dir(dir_path)

    def remove_dir(self, dir_path: str):
        p = Path(dir_path)
        if not p.exists():
            return
        # 对临时/输出目录不做回滚追踪
        if self._is_excluded(p):
            return self._base.remove_dir(str(p))
        # 递归安全删除文件，保留空目录（不强制删）
        self._safe_remove_dir(p)

    def _safe_remove_dir(self, p: Path):
        for item in p.iterdir():
            if item.is_file():
                if not self._is_ignored_file(item):
                    self._rb.safe_delete_file(item)
            elif item.is_dir():
                self._safe_remove_dir(item)
        # 尝试删除空目录（非必须）
        try:
            p.rmdir()
        except Exception:
            pass

    def create_temp_dir(self, prefix: str = "unifypy_") -> str:
        path = self._base.create_temp_dir(prefix)
        try:
            self._rb.track_dir_creation(Path(path))
        except Exception:
            pass
        return path


class AutoRollbackPlugin(BasePlugin):
    name = "auto_rollback"
    # 在 prepare(40) 之前安装包装，且晚于 config(20)/env(30)
    priority = 35

    def register(self, bus: EventBus):
        self._bus = bus
        bus.subscribe(ON_START, self.on_start, priority=18)
        bus.subscribe(PREPARE, self.on_prepare, priority=self.priority)
        bus.subscribe(ON_ERROR, self.on_error, priority=4)
        bus.subscribe(ON_SUCCESS, self.on_success, priority=91)

    def on_start(self, ctx):
        if getattr(ctx.args, "no_rollback", False):
            ctx.state["rollback_enabled"] = False
            return
        ctx.state["rollback_enabled"] = True
        ctx.state["rollback_manager"] = RollbackManager(ctx.project_dir, ctx.progress)
        # 清理老旧会话，仅保留最近 3 次
        try:
            rb = ctx.state["rollback_manager"]
            keep = getattr(ctx.args, "rollback_keep", 3) or 0
            if keep > 0:
                sessions = rb.list_rollback_sessions()
                if len(sessions) > keep:
                    for sid in sessions[keep:]:
                        # 删除旧备份与记录
                        try:
                            # 删除备份目录
                            backup_dir = rb.rollback_dir / f"backup_{sid}"
                            if backup_dir.exists():
                                import shutil
                                shutil.rmtree(backup_dir, ignore_errors=True)
                            # 删除操作日志
                            log_file = rb.rollback_dir / f"operations_{sid}.json"
                            if log_file.exists():
                                log_file.unlink()
                        except Exception:
                            pass
        except Exception:
            pass

    def on_prepare(self, ctx):
        if not ctx.state.get("rollback_enabled"):
            return
        rb = ctx.state.get("rollback_manager")
        if rb and ctx.file_ops:
            # 用包装替换文件操作
            excluded = [ctx.dist_dir, ctx.installer_dir, ctx.project_dir / ".unifypy", ctx.project_dir / ".unifypy_rollback", ctx.project_dir / "build"]
            ctx.file_ops = _RollbackFileOps(ctx.file_ops, rb, excluded_roots=excluded)

    def on_error(self, ctx):
        rb = ctx.state.get("rollback_manager")
        if not rb:
            return
        try:
            ok = rb.rollback()
        except Exception:
            ok = False
        # 无论回滚是否成功，都清理当前会话，避免堆积
        try:
            rb.cleanup()
        except Exception:
            pass

    def on_success(self, ctx):
        rb = ctx.state.get("rollback_manager")
        if not rb:
            return
        try:
            rb.cleanup()
        except Exception:
            pass
