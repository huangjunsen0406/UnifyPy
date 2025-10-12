#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交互式输入处理模块
提供统一的用户输入处理功能
"""

import sys
from typing import Dict, List, Optional

# 尝试导入平台相关的模块
try:
    import termios
    import tty
    HAS_TERMIOS = True
except ImportError:
    HAS_TERMIOS = False

try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False


class InputHandler:
    """用户输入处理器"""

    # ANSI 颜色
    COLORS = {
        'cyan': '\033[96m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'gray': '\033[90m',
        'red': '\033[91m',
        'reset': '\033[0m',
        'bold': '\033[1m',
    }

    @classmethod
    def _color(cls, color: str, text: str) -> str:
        """添加颜色"""
        return f"{cls.COLORS.get(color, '')}{text}{cls.COLORS['reset']}"

    @classmethod
    def info(cls, message: str):
        """显示信息"""
        print(f"{cls._color('blue', 'ℹ')} {cls._color('gray', message)}")

    @classmethod
    def success(cls, message: str):
        """显示成功信息"""
        print(f"{cls._color('green', '✓')} {message}")

    @classmethod
    def error(cls, message: str):
        """显示错误信息"""
        print(f"{cls._color('red', '✗')} {message}")

    @classmethod
    def text(
        cls,
        prompt: str,
        default: str = "",
        required: bool = False,
        help_text: str = ""
    ) -> str:
        """
        文本输入

        Args:
            prompt: 提示文本
            default: 默认值
            required: 是否必填
            help_text: 帮助文本

        Returns:
            用户输入的文本
        """
        while True:
            display = f"{cls._color('cyan', '?')} {cls._color('bold', prompt)}"

            if default:
                display += f": {cls._color('gray', f'({default})')}"

            display += f" {cls._color('gray', '›')} "

            value = input(display).strip()

            # 处理帮助请求
            if value in ["?", "？"] and help_text:
                cls.info(help_text)
                continue

            # 使用默认值
            if not value and default:
                return default

            # 验证必填
            if required and not value:
                cls.error("此项不能为空")
                continue

            return value

    @classmethod
    def _get_key(cls):
        """获取键盘输入（支持方向键）"""
        try:
            if sys.platform.startswith("win") and HAS_MSVCRT:
                key = msvcrt.getch()
                if key == b"\xe0":  # 特殊键前缀
                    key = msvcrt.getch()
                    if key == b"M":  # 右箭头
                        return "right"
                    elif key == b"K":  # 左箭头
                        return "left"
                elif key == b" ":  # 空格
                    return "space"
                elif key == b"\r":  # 回车
                    return "enter"
                elif key == b"\x1b":  # ESC
                    return "esc"
            else:
                # Unix/Linux/macOS
                if HAS_TERMIOS:
                    fd = sys.stdin.fileno()
                    old_settings = termios.tcgetattr(fd)
                    try:
                        tty.setraw(sys.stdin.fileno())
                        key = sys.stdin.read(1)

                        if key == "\x1b":  # ESC序列
                            try:
                                import fcntl
                                import os

                                fd = sys.stdin.fileno()
                                flags = fcntl.fcntl(fd, fcntl.F_GETFL)
                                fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                                try:
                                    char1 = sys.stdin.read(1)
                                    if char1 == "[":
                                        char2 = sys.stdin.read(1)
                                        if char2 == "C":  # 右箭头
                                            return "right"
                                        elif char2 == "D":  # 左箭头
                                            return "left"
                                except (OSError, IOError):
                                    pass
                                finally:
                                    fcntl.fcntl(fd, fcntl.F_SETFL, flags)
                            except ImportError:
                                pass

                            return "esc"
                        elif key == " ":
                            return "space"
                        elif key in ["\r", "\n"]:
                            return "enter"
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            pass

        return None

    @classmethod
    def confirm(
        cls,
        prompt: str,
        default: bool = True,
        help_text: str = ""
    ) -> bool:
        """
        确认输入（Yes/No）- 支持左右键盘选择

        Args:
            prompt: 提示文本
            default: 默认值
            help_text: 帮助文本

        Returns:
            True/False
        """
        # 当前选择状态
        current_choice = default

        # 隐藏光标
        sys.stdout.write('\033[?25l')
        sys.stdout.flush()

        try:
            while True:
                # 构建显示文本
                yes_text = "Yes" if current_choice else "yes"
                no_text = "No" if not current_choice else "no"

                # 高亮当前选择
                if current_choice:
                    yes_display = cls._color('green', f'> {yes_text}')
                    no_display = cls._color('gray', f'  {no_text}')
                else:
                    yes_display = cls._color('gray', f'  {yes_text}')
                    no_display = cls._color('green', f'> {no_text}')

                # 构建完整提示
                display = (
                    f"\r{cls._color('cyan', '?')} {cls._color('bold', prompt)}: "
                    f"{cls._color('gray', '›')} {yes_display} / {no_display} "
                    f"{cls._color('gray', '(Use arrow keys)')}"
                )

                # 打印当前状态（覆盖之前的行）
                sys.stdout.write('\033[K')  # 清除当前行
                sys.stdout.write(display)
                sys.stdout.flush()

                # 获取键盘输入
                key = cls._get_key()

                if key == "right":
                    # 右键：切换到 No
                    current_choice = False
                elif key == "left":
                    # 左键：切换到 Yes
                    current_choice = True
                elif key in ["enter", "space"]:
                    # 回车或空格：确认选择
                    print()  # 换行
                    return current_choice
                elif key == "esc":
                    # ESC：取消，返回默认值
                    print()  # 换行
                    return default

        finally:
            # 显示光标
            sys.stdout.write('\033[?25h')
            sys.stdout.flush()

    @classmethod
    def choice(
        cls,
        prompt: str,
        choices: Dict[str, str],
        default: str = None,
        help_text: str = ""
    ) -> str:
        """
        选择输入（单选）

        Args:
            prompt: 提示文本
            choices: 选项字典 {key: description}
            default: 默认值
            help_text: 帮助文本

        Returns:
            选中的 key
        """
        # 显示选项
        print(f"{cls._color('cyan', '?')} {cls._color('bold', prompt)}: "
              f"{cls._color('gray', '› (Use arrow-keys. Return to submit.)')}")

        for key, desc in choices.items():
            marker = "❯ " if key == default else "  "
            print(f"  {marker}{desc}")

        if help_text:
            print(f"  {cls._color('gray', help_text)}")

        while True:
            choice = input(f"选择 (默认{default}): ").strip()

            # 处理帮助请求
            if choice in ["?", "？"] and help_text:
                cls.info(help_text)
                continue

            # 使用默认值
            if not choice and default:
                choice = default

            # 验证选择
            if choice in choices:
                return choice
            else:
                valid_choices = ", ".join(choices.keys())
                cls.error(f"请输入有效选项 ({valid_choices})")

    @classmethod
    def list_input(
        cls,
        prompt: str,
        separator: str = ",",
        help_text: str = ""
    ) -> List[str]:
        """
        列表输入（逗号分隔）

        Args:
            prompt: 提示文本
            separator: 分隔符
            help_text: 帮助文本

        Returns:
            列表
        """
        while True:
            display = f"{cls._color('cyan', '?')} {cls._color('bold', prompt)}: {cls._color('gray', '›')} "

            text = input(display).strip()

            # 处理帮助请求
            if text in ["?", "？"] and help_text:
                cls.info(help_text)
                continue

            if not text:
                return []

            return [item.strip() for item in text.split(separator) if item.strip()]
