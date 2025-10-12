#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目目录扫描器
扫描项目中可打包的目录和文件
"""

from pathlib import Path
from typing import List, Dict, Any
import fnmatch


class ProjectScanner:
    """项目目录扫描器"""

    # 排除的目录（不应该打包的）
    EXCLUDED_DIRS = {
        '__pycache__', '.git', '.venv', 'venv', 'env', '.env',
        'node_modules', '.idea', '.vscode', '.pytest_cache',
        'build', 'dist', 'installer', '.DS_Store', '.eggs',
        '*.egg-info', '.tox', '.mypy_cache', '.ruff_cache',
        'htmlcov', '.coverage', '.cache', 'tmp', 'temp',
        '.github', '.gitlab', '.svn', '.hg'
    }

    # 常见的数据目录（优先推荐）
    COMMON_DATA_DIRS = {
        'assets', 'resources', 'data', 'static', 'public',
        'models', 'libs', 'src', 'app', 'core', 'config',
        'scripts', 'templates', 'locale', 'i18n', 'translations',
        'media', 'images', 'sounds', 'fonts'
    }

    @classmethod
    def scan_directories(cls, project_dir: Path) -> List[Dict[str, Any]]:
        """
        扫描项目目录，返回可打包的目录列表

        Args:
            project_dir: 项目根目录

        Returns:
            目录列表，每个目录包含 value, label, hint, checked 字段
        """
        directories = []

        # 遍历项目根目录的一级子目录
        try:
            for item in sorted(project_dir.iterdir()):
                if not item.is_dir():
                    continue

                dir_name = item.name

                # 排除不应该打包的目录
                if cls._should_exclude(dir_name):
                    continue

                # 判断是否是常见数据目录（推荐选中）
                is_common = dir_name in cls.COMMON_DATA_DIRS

                # 获取目录大小和文件数
                size_info = cls._get_dir_info(item)

                directories.append({
                    'value': dir_name,
                    'label': f"{dir_name}{'  (推荐)' if is_common else ''}",
                    'hint': size_info,
                    'checked': is_common  # 常见目录默认选中
                })

        except (OSError, PermissionError) as e:
            print(f"⚠️  扫描目录时出错: {e}")

        return directories

    @classmethod
    def _should_exclude(cls, dir_name: str) -> bool:
        """判断目录是否应该排除"""
        # 隐藏目录
        if dir_name.startswith('.'):
            return True

        # 排除列表中的目录
        if dir_name in cls.EXCLUDED_DIRS:
            return True

        # 匹配通配符
        for pattern in cls.EXCLUDED_DIRS:
            if fnmatch.fnmatch(dir_name, pattern):
                return True

        return False

    @classmethod
    def _get_dir_info(cls, dir_path: Path) -> str:
        """获取目录信息（大小和文件数）"""
        try:
            file_count = 0
            total_size = 0

            # 遍历目录中的所有文件
            for item in dir_path.rglob('*'):
                if item.is_file():
                    file_count += 1
                    try:
                        total_size += item.stat().st_size
                    except (OSError, PermissionError):
                        pass

            # 格式化大小
            size_str = cls._format_size(total_size)

            return f"{file_count} files, {size_str}"

        except (OSError, PermissionError):
            return "inaccessible"

    @classmethod
    def _format_size(cls, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
