#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件操作工具 提供跨平台的文件和目录操作功能.
"""

import os
import platform
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileOperations:
    """
    文件操作工具类.
    """

    def __init__(self):
        """
        初始化文件操作工具.
        """
        self.current_platform = platform.system().lower()

    def create_temp_dir(self, prefix: str = "unifypy_") -> str:
        """创建临时目录.

        Args:
            prefix: 目录名前缀

        Returns:
            str: 临时目录路径
        """
        return tempfile.mkdtemp(prefix=prefix)

    def cleanup_temp_dir(self, temp_dir: str):
        """清理临时目录.

        Args:
            temp_dir: 临时目录路径
        """
        if os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"警告: 无法完全清理临时目录 {temp_dir}: {e}")

    def ensure_dir(self, dir_path: str):
        """确保目录存在，不存在则创建.

        Args:
            dir_path: 目录路径
        """
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    def copy_file(self, src: str, dst: str):
        """复制文件.

        Args:
            src: 源文件路径
            dst: 目标文件路径
        """
        self.ensure_dir(os.path.dirname(dst))
        shutil.copy2(src, dst)

    def copy_tree(self, src: str, dst: str):
        """复制目录树.

        Args:
            src: 源目录路径
            dst: 目标目录路径
        """
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

    def move_file(self, src: str, dst: str):
        """移动文件.

        Args:
            src: 源文件路径
            dst: 目标文件路径
        """
        self.ensure_dir(os.path.dirname(dst))
        shutil.move(src, dst)

    def remove_file(self, file_path: str):
        """删除文件.

        Args:
            file_path: 文件路径
        """
        if os.path.exists(file_path):
            os.remove(file_path)

    def remove_dir(self, dir_path: str):
        """删除目录.

        Args:
            dir_path: 目录路径
        """
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)

    def get_file_size(self, file_path: str) -> int:
        """获取文件大小.

        Args:
            file_path: 文件路径

        Returns:
            int: 文件大小（字节）
        """
        return os.path.getsize(file_path) if os.path.exists(file_path) else 0

    def format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小.

        Args:
            size_bytes: 字节数

        Returns:
            str: 格式化的大小字符串
        """
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def find_files(
        self, directory: str, pattern: str = "*", recursive: bool = True
    ) -> List[str]:
        """查找文件.

        Args:
            directory: 搜索目录
            pattern: 文件名模式
            recursive: 是否递归搜索

        Returns:
            List[str]: 匹配的文件路径列表
        """
        from pathlib import Path

        path = Path(directory)
        if not path.exists():
            return []

        files = []
        if recursive:
            for file_path in path.rglob(pattern):
                if file_path.is_file():
                    files.append(str(file_path))
        else:
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    files.append(str(file_path))

        return files

    def get_executable_extension(self) -> str:
        """获取当前平台的可执行文件扩展名.

        Returns:
            str: 扩展名
        """
        return ".exe" if self.current_platform == "windows" else ""

    def make_executable(self, file_path: str):
        """设置文件为可执行.

        Args:
            file_path: 文件路径
        """
        if os.path.exists(file_path):
            current_mode = os.stat(file_path).st_mode
            os.chmod(file_path, current_mode | 0o755)

    def check_disk_space(self, path: str, required_mb: int = 100) -> bool:
        """检查磁盘空间是否足够.

        Args:
            path: 路径
            required_mb: 所需空间（MB）

        Returns:
            bool: 空间是否足够
        """
        try:
            statvfs = os.statvfs(path) if hasattr(os, "statvfs") else None
            if statvfs:
                # Unix/Linux/macOS
                free_bytes = statvfs.f_frsize * statvfs.f_bavail
            else:
                # Windows
                import shutil

                free_bytes = shutil.disk_usage(path).free

            required_bytes = required_mb * 1024 * 1024
            return free_bytes >= required_bytes
        except:
            return True  # 无法检查时假设有足够空间

    def create_version_info_file(self, app_info: Dict[str, Any], output_path: str):
        """创建Windows版本信息文件.

        Args:
            app_info: 应用信息字典
            output_path: 输出文件路径
        """
        version_template = """# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers={file_version},
    prodvers={product_version},
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x4,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', '{company}'),
        StringStruct('FileDescription', '{description}'),
        StringStruct('FileVersion', '{file_version_str}'),
        StringStruct('InternalName', '{internal_name}'),
        StringStruct('LegalCopyright', '{copyright}'),
        StringStruct('OriginalFilename', '{original_filename}'),
        StringStruct('ProductName', '{product_name}'),
        StringStruct('ProductVersion', '{product_version_str}')])
      ]), 
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)"""

        # 解析版本号
        version = app_info.get("version", "1.0.0")
        version_parts = version.split(".")
        while len(version_parts) < 4:
            version_parts.append("0")

        file_version = tuple(int(part) for part in version_parts[:4])
        product_version = file_version

        # 填充模板
        version_info = version_template.format(
            file_version=file_version,
            product_version=product_version,
            company=app_info.get("publisher", "Unknown Publisher"),
            description=app_info.get(
                "display_name", app_info.get("name", "Application")
            ),
            file_version_str=version,
            internal_name=app_info.get("name", "app"),
            copyright=f"Copyright © {app_info.get('publisher', 'Unknown Publisher')}",
            original_filename=f"{app_info.get('name', 'app')}.exe",
            product_name=app_info.get(
                "display_name", app_info.get("name", "Application")
            ),
            product_version_str=version,
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(version_info)

    def normalize_path(self, path: str, target_platform: Optional[str] = None) -> str:
        """规范化路径格式.

        Args:
            path: 原始路径
            target_platform: 目标平台，None表示当前平台

        Returns:
            str: 规范化的路径
        """
        platform = target_platform or self.current_platform

        if platform == "windows":
            return path.replace("/", "\\")
        else:
            return path.replace("\\", "/")

    def get_relative_path(self, path: str, base_path: str) -> str:
        """获取相对路径.

        Args:
            path: 目标路径
            base_path: 基准路径

        Returns:
            str: 相对路径
        """
        return os.path.relpath(path, base_path)

    def resolve_path(self, path: str, base_path: Optional[str] = None) -> str:
        """解析路径为绝对路径.

        Args:
            path: 路径
            base_path: 基准路径

        Returns:
            str: 绝对路径
        """
        if os.path.isabs(path):
            return path

        if base_path:
            return os.path.abspath(os.path.join(base_path, path))
        else:
            return os.path.abspath(path)
