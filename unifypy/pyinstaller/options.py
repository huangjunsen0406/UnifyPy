#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PyInstaller option constant maps (extracted from config_builder)."""

# 完整的PyInstaller选项映射
PYINSTALLER_OPTIONS = {
    # 基本选项
    "onefile": "--onefile",
    "onedir": "--onedir",
    "windowed": "--windowed",
    "console": "--console",
    "name": "--name",
    "icon": "--icon",
    # 路径选项
    "distpath": "--distpath",
    "workpath": "--workpath",
    "specpath": "--specpath",
    # 包含/排除选项
    "add_data": "--add-data",
    "add_binary": "--add-binary",
    "hidden_import": "--hidden-import",
    "exclude_module": "--exclude-module",
    "additional_hooks_dir": "--additional-hooks-dir",
    "runtime_hook": "--runtime-hook",
    "collect_submodules": "--collect-submodules",
    "collect_data": "--collect-data",
    "collect_binaries": "--collect-binaries",
    "collect_all": "--collect-all",
    "copy_metadata": "--copy-metadata",
    "recursive_copy_metadata": "--recursive-copy-metadata",
    # 高级选项
    "splash": "--splash",
    "version_file": "--version-file",
    "manifest": "--manifest",
    "resource": "--resource",
    "uac_admin": "--uac-admin",
    "uac_uiaccess": "--uac-uiaccess",
    # 压缩和优化选项
    "upx_dir": "--upx-dir",
    "upx_exclude": "--upx-exclude",
    "noupx": "--noupx",
    "strip": "--strip",
    "debug": "--debug",
    "optimize": "--optimize",
    # 构建选项
    "clean": "--clean",
    "noconfirm": "--noconfirm",
    "ascii": "--ascii",
    "key": "--key",
    "contents_directory": "--contents-directory",
    # 日志选项
    "log_level": "--log-level",
    "quiet": "--quiet",
    # 兼容性选项
    "osx_bundle_identifier": "--osx-bundle-identifier",
    "target_architecture": "--target-architecture",
    "codesign_identity": "--codesign-identity",
    "osx_entitlements_file": "--osx-entitlements-file",
}

# 布尔类型选项（不需要值）
BOOLEAN_OPTIONS = {
    "onefile",
    "onedir",
    "windowed",
    "console",
    "clean",
    "noconfirm",
    "debug",
    "strip",
    "noupx",
    "ascii",
    "uac_admin",
    "uac_uiaccess",
    "quiet",
}

# 列表类型选项（可以多次指定）
LIST_OPTIONS = {
    "add_data",
    "add_binary",
    "hidden_import",
    "exclude_module",
    "additional_hooks_dir",
    "runtime_hook",
    "collect_submodules",
    "collect_data",
    "collect_binaries",
    "collect_all",
    "copy_metadata",
    "recursive_copy_metadata",
    "upx_exclude",
    "resource",
}
