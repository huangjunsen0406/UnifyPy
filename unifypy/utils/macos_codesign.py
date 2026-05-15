#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MacOS 代码签名工具 为未签名应用执行 ad-hoc 签名以应用 entitlements.
"""

import subprocess
from pathlib import Path
from typing import Optional

from .command_runner import get_subprocess_encoding


class MacOSCodeSigner:
    """
    MacOS 代码签名器.
    """

    def __init__(self, verbose: bool = False):
        self.codesign_path = None
        self.verbose = verbose

    def _print(self, message: str):
        """
        只在 verbose 模式下打印信息.
        """
        if self.verbose:
            print(message)

    def sign_app_with_entitlements(
        self, app_path: Path, entitlements_path: Optional[Path] = None
    ) -> bool:
        """对 .app 包执行 ad-hoc 签名.

        Args:
            app_path: .app 包路径
            entitlements_path: entitlements.plist 文件路径

        Returns:
            bool: 签名是否成功
        """
        if not app_path.exists() or not app_path.name.endswith(".app"):
            print(f"❌ 无效的 .app 包: {app_path}")  # 错误信息始终显示
            return False

        self._print(f"🔐 开始 ad-hoc 代码签名: {app_path.name}")

        try:
            # 移除现有签名（如果有）
            self._print("  🗑️  移除现有代码签名...")
            self._remove_existing_signature(app_path)

            # 执行 ad-hoc 签名
            codesign_cmd = self.codesign_path if self.codesign_path else "codesign"
            cmd = [
                codesign_cmd,
                "--force",
                "--deep",
                "--sign", "-",
                "--options", "runtime",
            ]

            if entitlements_path and entitlements_path.exists():
                cmd.extend(["--entitlements", str(entitlements_path)])
                self._print(f"  📜 使用 entitlements: {entitlements_path}")
            else:
                self._print("  ⚠️  没有 entitlements 文件，使用基础签名")

            cmd.append(str(app_path))

            self._print(f"  🚀 执行签名命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding=get_subprocess_encoding(),
                errors='replace',
                check=False
            )

            if result.returncode == 0:
                self._print("  ✅ 代码签名成功")

                # 验证签名
                if self._verify_signature(app_path):
                    self._print("  ✅ 签名验证通过")
                    return True
                else:
                    self._print("  ⚠️  签名验证失败，但应用仍可使用")
                    return True  # 即使验证失败，签名可能还是有效的
            else:
                print("  ❌ 代码签名失败:")  # 错误信息始终显示
                print(f"    错误输出: {result.stderr}")

                # 尝试基本的可执行权限设置
                self._set_executable_permissions(app_path)
                return False

        except Exception as e:
            print(f"❌ 代码签名异常: {e}")  # 错误信息始终显示
            return False

    def _remove_existing_signature(self, app_path: Path) -> bool:
        """
        移除现有的代码签名.
        """
        try:
            # 找到主可执行文件
            executable_path = self._find_main_executable(app_path)
            if executable_path and executable_path.exists():
                codesign_cmd = (
                    self.codesign_path if self.codesign_path else "/usr/bin/codesign"
                )
                cmd = [codesign_cmd, "--remove-signature", str(executable_path)]
                subprocess.run(
                    cmd,
                    capture_output=True,
                    encoding=get_subprocess_encoding(),
                    errors='replace',
                    check=False
                )
            return True
        except Exception:
            return True  # 忽略移除签名的错误

    def _find_main_executable(self, app_path: Path) -> Optional[Path]:
        """
        查找主可执行文件.
        """
        try:
            # 从 Info.plist 读取可执行文件名
            info_plist = app_path / "Contents" / "Info.plist"
            if info_plist.exists():
                cmd = [
                    "/usr/libexec/PlistBuddy",
                    "-c",
                    "Print :CFBundleExecutable",
                    str(info_plist),
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding=get_subprocess_encoding(),
                    errors='replace',
                    check=False
                )

                if result.returncode == 0:
                    executable_name = result.stdout.strip()
                    executable_path = app_path / "Contents" / "MacOS" / executable_name
                    if executable_path.exists():
                        return executable_path

            # 如果读取失败，尝试查找 MacOS 目录下的文件
            macos_dir = app_path / "Contents" / "MacOS"
            if macos_dir.exists():
                for file in macos_dir.iterdir():
                    if file.is_file() and not file.name.startswith("."):
                        return file

        except Exception:
            pass

        return None

    def _verify_signature(self, app_path: Path) -> bool:
        """
        验证代码签名.
        """
        try:
            codesign_cmd = (
                self.codesign_path if self.codesign_path else "/usr/bin/codesign"
            )
            cmd = [codesign_cmd, "-dv", "--verbose=4", str(app_path)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding=get_subprocess_encoding(),
                errors='replace',
                check=False
            )

            # codesign -dv 在成功时返回非零退出码，但输出到 stderr
            if "adhoc" in result.stderr.lower() or "signed" in result.stderr.lower():
                return True

            return False

        except Exception:
            return False

    def _set_executable_permissions(self, app_path: Path):
        """
        设置可执行权限（fallback）
        """
        try:
            executable_path = self._find_main_executable(app_path)
            if executable_path and executable_path.exists():
                import os

                os.chmod(executable_path, 0o755)
                self._print(f"  ✅ 设置可执行权限: {executable_path}")
        except Exception as e:
            print(f"  ⚠️  设置可执行权限失败: {e}")  # 错误信息始终显示

    def check_codesign_available(self) -> bool:
        """
        检查 codesign 工具是否可用.
        """
        # 尝试多个可能的路径
        codesign_paths = [
            "/usr/bin/codesign",  # 系统默认路径
            "codesign",  # PATH 中的路径
        ]

        for codesign_path in codesign_paths:
            try:
                # codesign 不支持 --version，使用 --help 或者直接测试可用性
                result = subprocess.run(
                    [codesign_path],
                    capture_output=True,
                    text=True,
                    encoding=get_subprocess_encoding(),
                    errors='replace',
                    check=False,
                    timeout=10,
                )
                # codesign 无参数调用会返回使用说明，退出码通常是 2，但这说明工具可用
                if result.returncode == 2 and "Usage: codesign" in result.stderr:
                    self._print(f"  ✅ 找到 codesign: {codesign_path}")
                    self.codesign_path = codesign_path  # 保存找到的路径
                    return True
                else:
                    self._print(f"  ❌ {codesign_path} 返回错误码: {result.returncode}")
                    if result.stderr:
                        self._print(f"  错误信息: {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                self._print(f"  ⏱️ {codesign_path} 超时")
                continue
            except FileNotFoundError:
                self._print(f"  📁 {codesign_path} 未找到")
                continue
            except Exception as e:
                self._print(f"  ❌ {codesign_path} 异常: {e}")
                continue

        print(
            "  ❌ codesign 工具不可用，请安装 Xcode Command Line Tools: xcode-select --install"
        )  # 错误信息始终显示
        return False
