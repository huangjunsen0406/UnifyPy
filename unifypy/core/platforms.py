#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
平台与架构规范化工具。

统一对外平台键：windows / macos / linux
统一对外架构键：x64 / arm64（仅支持 64 位；不支持 32 位/armv7）
"""

import platform as _platform
from typing import Optional


# 对外平台名常量
PLATFORM_WINDOWS = "windows"
PLATFORM_MACOS = "macos"
PLATFORM_LINUX = "linux"


def normalize_platform(system: Optional[str] = None) -> str:
    """将系统平台规范化为 windows/macos/linux。

    Args:
        system: 原始平台字符串（可选）；默认读取 platform.system().lower()
    """
    s = (system or _platform.system()).lower()
    if s == "darwin":
        return PLATFORM_MACOS
    if s.startswith("win"):
        return PLATFORM_WINDOWS
    if s == "linux":
        return PLATFORM_LINUX
    # 兜底：按 linux 处理
    return PLATFORM_LINUX


def normalize_arch(machine: Optional[str] = None) -> str:
    """将 CPU 架构规范化为 x64/arm64（仅 64 位）。

    映射：
    - x86_64/amd64 → x64
    - aarch64/arm64/armv8* → arm64
    其他（如 armv7/armhf/i386 等 32 位）均视为不支持并抛出异常。
    """
    m = (machine or _platform.machine()).lower()
    if m in ("x86_64", "amd64"):
        return "x64"
    if m in ("aarch64", "arm64", "armv8", "armv8l"):
        return "arm64"
    # 只支持 64 位架构
    raise ValueError(f"不支持的架构: {m}（仅支持 x64/arm64）")


def is_supported_arch(arch: Optional[str] = None) -> bool:
    """是否为推荐支持的架构（x64/arm64）。
    """
    a = arch.lower() if arch else normalize_arch()
    return a in ("x64", "arm64")
