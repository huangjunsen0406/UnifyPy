#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
环境管理器 处理构建环境的准备和清理.
支持现代化的规范化架构映射系统 (2024 标准)
"""

import platform
import subprocess
import os
from pathlib import Path
from typing import Any, Dict, Optional


class EnvironmentManager:
    """
    环境管理器 - 支持规范化架构映射和现代分发标准.
    
    内部架构键规范:
    - win-x64, win-arm64
    - mac-arm64, mac-x64  
    - linux-x64-glibc, linux-arm64-glibc
    - linux-x64-musl, linux-arm64-musl
    """

    def __init__(self, project_dir: str):
        """初始化环境管理器.

        Args:
            project_dir: 项目目录
        """
        self.project_dir = Path(project_dir).resolve()
        self.current_platform = self._detect_platform()
        self.current_arch = self._detect_raw_architecture()
        self.normalized_arch = self._normalize_architecture()
        self.c_runtime = self._detect_c_runtime() if self.current_platform == "linux" else None
        self.internal_key = self._generate_internal_key()

    def _detect_platform(self) -> str:
        """
        检测当前平台.
        """
        system = platform.system().lower()
        if system == "darwin":
            return "mac"
        elif system == "windows":
            return "win"
        elif system == "linux":
            return "linux"
        else:
            return system

    def _detect_raw_architecture(self) -> str:
        """
        检测原始架构标识.
        """
        return platform.machine().lower()

    def _normalize_architecture(self) -> str:
        """
        将各种系统返回的机型字符串规范化为内部架构键.
        
        Returns:
            str: 规范化的架构标识 (x64, arm64)
        """
        machine = self.current_arch
        
        # AMD64|x86_64 → x64
        if machine in ["x86_64", "amd64"]:
            return "x64"
        
        # ARM64|aarch64|arm64 → arm64  
        elif machine in ["aarch64", "arm64", "armv8", "armv8l"]:
            return "arm64"
        
        # 不再支持 32 位架构
        elif machine in ["i386", "i686", "i586", "armv7", "armv7l", "armhf", "arm"]:
            raise ValueError(f"不支持的 32 位架构: {machine}。UnifyPy 2.0 仅支持 64 位架构。")
        
        else:
            raise ValueError(f"不支持的架构: {machine}")

    def _detect_c_runtime(self) -> Optional[str]:
        """
        检测 Linux C 运行时 (glibc/musl).
        
        Returns:
            str: 'glibc' 或 'musl'
        """
        if self.current_platform != "linux":
            return None
            
        try:
            # 检测 ldd --version 是否包含 musl
            result = subprocess.run(
                ["ldd", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            output = result.stderr.lower() + result.stdout.lower()
            
            if "musl" in output:
                return "musl"
            else:
                return "glibc"  # 默认为 glibc (manylinux)
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # 备用检测方法：检查 /lib/libc.musl* 文件
            try:
                musl_files = list(Path("/lib").glob("libc.musl*"))
                if musl_files:
                    return "musl"
            except:
                pass
            
            # 默认假设为 glibc
            return "glibc"

    def _is_rosetta(self) -> bool:
        """
        检测是否在 macOS Rosetta 下运行.
        
        Returns:
            bool: 是否在 Rosetta 下运行
        """
        if self.current_platform != "mac":
            return False
            
        try:
            result = subprocess.run(
                ["sysctl", "-in", "sysctl.proc_translated"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() == "1"
        except:
            return False

    def _generate_internal_key(self) -> str:
        """
        生成规范化的内部架构键.
        
        Returns:
            str: 内部架构键 (如 mac-arm64, linux-x64-glibc)
        """
        base_key = f"{self.current_platform}-{self.normalized_arch}"
        
        # Linux 需要添加 C 运行时标识
        if self.current_platform == "linux":
            base_key += f"-{self.c_runtime}"
        
        return base_key

    def get_internal_key(self) -> str:
        """
        获取当前环境的内部架构键.
        
        Returns:
            str: 内部架构键
        """
        return self.internal_key

    def get_rosetta_info(self) -> Dict[str, Any]:
        """
        获取 Rosetta 相关信息.
        
        Returns:
            Dict: Rosetta 信息
        """
        if self.current_platform != "mac":
            return {"supported": False, "running": False}
            
        is_rosetta = self._is_rosetta()
        return {
            "supported": True,
            "running": is_rosetta,
            "native_arch": "arm64" if self.normalized_arch == "x64" and is_rosetta else self.normalized_arch,
            "recommendation": "建议下载 arm64 版本" if is_rosetta else f"使用 {self.normalized_arch} 版本"
        }

    def get_arch_for_format(self, format_type: str) -> str:
        """
        根据打包格式获取标准化的架构名称 (仅支持 64 位).
        
        Args:
            format_type: 打包格式 (deb, rpm, appimage, dmg, exe, zip)
            
        Returns:
            str: 对应格式的架构名称
        """
        # 只支持 64 位架构
        if self.normalized_arch == "x64":
            if format_type in ["deb"]:
                return "amd64"  # Debian/Ubuntu 包名
            elif format_type in ["rpm"]:
                return "x86_64"  # RPM 包名
            elif format_type in ["appimage", "dmg", "exe"]:
                return "x86_64"  # 通用标准
            else:
                return "x86_64"
        
        elif self.normalized_arch == "arm64":
            if format_type in ["deb"]:
                return "arm64"  # Debian/Ubuntu 包名
            elif format_type in ["rpm"]:
                return "aarch64"  # RPM 包名 
            elif format_type in ["appimage", "dmg", "exe"]:
                return "aarch64"  # 通用标准
            else:
                return "arm64"
        
        else:
            raise ValueError(f"不支持的架构: {self.normalized_arch}")

    def get_package_filename_arch(self, format_type: str) -> str:
        """
        获取用于包文件名的架构标识.
        
        Args:
            format_type: 打包格式
            
        Returns:
            str: 用于文件名的架构标识
        """
        return self.get_arch_for_format(format_type)

    def get_modern_filename(self, app_name: str, version: str, format_type: str) -> str:
        """
        生成现代化的文件名 (使用内部架构键).
        
        Args:
            app_name: 应用名称
            version: 版本号
            format_type: 文件格式 (zip, tar.gz, dmg, exe)
            
        Returns:
            str: 现代化的文件名
        """
        # 使用内部架构键作为文件名的一部分
        return f"{app_name}-{version}-{self.internal_key}.{format_type}"

    def get_legacy_format_filename(self, app_name: str, version: str, format_type: str) -> str:
        """
        生成传统格式的文件名 (兼容现有系统).
        
        Args:
            app_name: 应用名称  
            version: 版本号
            format_type: 打包格式 (deb, rpm, appimage)
            
        Returns:
            str: 传统格式的文件名
        """
        arch = self.get_arch_for_format(format_type)
        
        if format_type == "deb":
            return f"{app_name}_{version}_{arch}.deb"
        elif format_type == "rpm":
            return f"{app_name}-{version}-1.{arch}.rpm"
        elif format_type == "appimage":
            return f"{app_name}-{version}-{arch}.AppImage"
        else:
            return f"{app_name}-{version}-{arch}.{format_type}"

    def is_supported_architecture(self) -> bool:
        """
        检查当前架构是否受支持 (仅 64 位).
        
        Returns:
            bool: 是否支持当前架构
        """
        try:
            # 如果可以成功规范化架构，则支持
            self._normalize_architecture()
            return True
        except ValueError:
            return False

    def get_manylinux_tag(self) -> str:
        """
        获取 Python manylinux 标签 (2024 标准).
        
        Returns:
            str: manylinux 标签
        """
        if self.current_platform != "linux":
            return ""
            
        arch = self.get_arch_for_format("deb")  # 使用 DEB 格式的架构名
        
        if self.c_runtime == "musl":
            # musllinux 标签 (Alpine 等)
            return f"musllinux_1_2_{arch}"
        else:
            # manylinux 标签 (glibc)
            # 2024 标准推荐使用 manylinux_2_28
            return f"manylinux_2_28_{arch}"

    def get_rust_target_triple(self) -> str:
        """
        获取 Rust 目标三元组.
        
        Returns:
            str: Rust target triple
        """
        if self.current_platform == "linux":
            if self.normalized_arch == "x64":
                if self.c_runtime == "musl":
                    return "x86_64-unknown-linux-musl"
                else:
                    return "x86_64-unknown-linux-gnu"
            elif self.normalized_arch == "arm64":
                if self.c_runtime == "musl":
                    return "aarch64-unknown-linux-musl"
                else:
                    return "aarch64-unknown-linux-gnu"
                    
        elif self.current_platform == "mac":
            if self.normalized_arch == "x64":
                return "x86_64-apple-darwin"
            elif self.normalized_arch == "arm64":
                return "aarch64-apple-darwin"
                
        elif self.current_platform == "win":
            if self.normalized_arch == "x64":
                return "x86_64-pc-windows-msvc"
            elif self.normalized_arch == "arm64":
                return "aarch64-pc-windows-msvc"
        
        raise ValueError(f"不支持的平台/架构组合: {self.current_platform}-{self.normalized_arch}")

    def get_recommended_targets(self) -> Dict[str, str]:
        """
        获取推荐的打包目标 (2024 标准).
        
        Returns:
            Dict: 推荐的打包目标
        """
        targets = {
            "primary": self.internal_key,
            "rust_triple": self.get_rust_target_triple(),
        }
        
        if self.current_platform == "linux":
            targets["manylinux"] = self.get_manylinux_tag()
            
        return targets

    def get_platform_info(self) -> Dict[str, Any]:
        """获取平台信息 (现代化版本).

        Returns:
            Dict[str, Any]: 平台信息字典
        """
        info = {
            "platform": self.current_platform,
            "raw_architecture": self.current_arch,
            "normalized_architecture": self.normalized_arch,
            "internal_key": self.internal_key,
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "supported": self.is_supported_architecture(),
        }
        
        # Linux 特定信息
        if self.current_platform == "linux":
            info.update({
                "c_runtime": self.c_runtime,
                "manylinux_tag": self.get_manylinux_tag(),
            })
        
        # macOS 特定信息  
        if self.current_platform == "mac":
            rosetta_info = self.get_rosetta_info()
            info.update({
                "rosetta": rosetta_info,
            })
        
        # 添加推荐目标
        info["recommended_targets"] = self.get_recommended_targets()
        
        return info

    def check_prerequisites(self) -> Dict[str, bool]:
        """检查构建前提条件 (现代化版本).

        Returns:
            Dict[str, bool]: 检查结果字典
        """
        results = {}

        # 检查Python版本 (UnifyPy 2.0 要求 Python 3.8+)
        import sys
        python_version = sys.version_info
        results["python_version"] = python_version >= (3, 8)

        # 检查架构支持
        results["architecture_supported"] = self.is_supported_architecture()

        # 检查必要库
        libraries = ["pyinstaller", "rich", "requests"]
        for lib in libraries:
            try:
                __import__(lib)
                results[lib] = True
            except ImportError:
                results[lib] = False

        return results

    def get_recommended_settings(self) -> Dict[str, Any]:
        """获取推荐的平台设置 (现代化版本).

        Returns:
            Dict[str, Any]: 推荐设置
        """
        settings = {
            "internal_key": self.internal_key,
            "architecture": self.normalized_arch,
        }

        if self.current_platform == "win":
            settings.update({
                "pyinstaller": {
                    "windowed": True, 
                    "icon": "app.ico",
                    "target_architecture": self.normalized_arch
                },
                "installer_type": "inno_setup",
                "recommended_formats": ["exe"],
            })
        elif self.current_platform == "mac":
            settings.update({
                "pyinstaller": {
                    "windowed": True,
                    "osx_bundle_identifier": "com.example.app",
                    "target_architecture": self.normalized_arch
                },
                "installer_type": "dmg",
                "recommended_formats": ["dmg"],
            })
            
            # Rosetta 特殊建议
            rosetta_info = self.get_rosetta_info()
            if rosetta_info["running"]:
                settings["rosetta_notice"] = "在 Rosetta 下运行，建议构建 arm64 和 universal2 版本"
                
        elif self.current_platform == "linux":
            settings.update({
                "pyinstaller": {
                    "strip": True,
                    "target_architecture": self.normalized_arch
                },
                "installer_type": "deb",  # 默认推荐 DEB
                "recommended_formats": ["deb", "appimage"],
                "c_runtime": self.c_runtime,
                "manylinux_compatible": self.c_runtime == "glibc",
            })

        return settings

    def get_build_recommendations(self) -> Dict[str, Any]:
        """
        获取 2024 年构建和发布建议.
        
        Returns:
            Dict: 构建建议
        """
        recommendations = {
            "primary_targets": [],
            "optional_targets": [],
            "naming_examples": {},
            "compatibility_notes": []
        }
        
        # 主要构建目标 (6 档标准)
        if self.current_platform == "win":
            recommendations["primary_targets"] = ["win-x64", "win-arm64"]
            recommendations["naming_examples"] = {
                "modern": f"myapp-1.2.3-{self.internal_key}.zip",
                "traditional": "myapp-1.2.3.exe"
            }
            
        elif self.current_platform == "mac":
            recommendations["primary_targets"] = ["mac-arm64", "mac-x64"]
            recommendations["optional_targets"] = ["mac-universal2"]
            recommendations["naming_examples"] = {
                "modern": f"myapp-1.2.3-{self.internal_key}.dmg",
                "universal": "myapp-1.2.3-mac-universal2.dmg"
            }
            
        elif self.current_platform == "linux":
            recommendations["primary_targets"] = [f"linux-{self.normalized_arch}-glibc", f"linux-{self.normalized_arch}-musl"]
            
            if self.c_runtime == "glibc":
                recommendations["compatibility_notes"].append("优先 manylinux_2_28，老发行版需求时加 manylinux_2_17")
            else:
                recommendations["compatibility_notes"].append("Alpine 用户使用 musllinux 变体")
                
            recommendations["naming_examples"] = {
                "modern": f"myapp-1.2.3-{self.internal_key}.tar.gz",
                "deb": f"myapp_1.2.3_{self.get_arch_for_format('deb')}.deb",
                "appimage": f"myapp-1.2.3-{self.get_arch_for_format('appimage')}.AppImage"
            }
        
        return recommendations
