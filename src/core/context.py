#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
构建上下文：贯穿生命周期的共享状态与依赖。
"""

from pathlib import Path
from typing import Any, Dict, Optional


class BuildContext:
    def __init__(self, args: Any):
        self.args = args
        self.project_dir: Path = Path(getattr(args, "project_dir", ".")).resolve()

        # 运行期组件（由插件填充）
        self.progress = None
        self.runner = None
        self.file_ops = None
        self.tool_manager = None
        self.packager_registry = None
        self.config = None
        self.env_manager = None
        self.cache_manager = None

        # 目录
        self.temp_dir: Optional[Path] = None
        self.dist_dir: Path = self.project_dir / "dist"
        self.installer_dir: Path = self.project_dir / "installer"

        # 其他
        self.errors = []  # [(event, Exception)]
        self.state: Dict[str, Any] = {}
        self.exit_code: int = 0
        self.should_exit: bool = False

