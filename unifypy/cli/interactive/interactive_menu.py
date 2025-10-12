# -*- coding: utf-8 -*-
"""
交互式终端菜单模块
支持上下键导航、空格键选择、回车键确认
"""

import sys
from typing import List, Tuple

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


class InteractiveMenu:
    """交互式多选菜单"""

    def __init__(self):
        self.selected_items = set()
        self.current_index = 0
        self._ansi_enabled = False

    def get_key(self):
        """获取用户按键，包含错误处理"""
        try:
            if sys.platform.startswith("win") and HAS_MSVCRT:
                key = msvcrt.getch()
                if key == b"\xe0":  # 特殊键前缀
                    key = msvcrt.getch()
                    if key == b"H":  # 上箭头
                        return "up"
                    elif key == b"P":  # 下箭头
                        return "down"
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
                            # 不使用select，直接尝试读取后续字符
                            try:
                                # 设置非阻塞模式读取
                                import fcntl
                                import os

                                fd = sys.stdin.fileno()
                                flags = fcntl.fcntl(fd, fcntl.F_GETFL)
                                fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                                try:
                                    char1 = sys.stdin.read(1)
                                    if char1 == "[":
                                        char2 = sys.stdin.read(1)
                                        if char2 == "A":  # 上箭头
                                            return "up"
                                        elif char2 == "B":  # 下箭头
                                            return "down"
                                        elif char2 == "C":  # 右箭头
                                            return "right"
                                        elif char2 == "D":  # 左箭头
                                            return "left"
                                except (OSError, IOError):
                                    # 没有更多字符可读，是单独的ESC键
                                    pass
                                finally:
                                    # 恢复阻塞模式
                                    fcntl.fcntl(fd, fcntl.F_SETFL, flags)

                            except ImportError:
                                # 如果fcntl不可用，使用原来的select方法
                                import select

                                if select.select([sys.stdin], [], [], 0.05)[0]:
                                    char1 = sys.stdin.read(1)
                                    if char1 == "[":
                                        char2 = sys.stdin.read(1)
                                        if char2 == "A":  # 上箭头
                                            return "up"
                                        elif char2 == "B":  # 下箭头
                                            return "down"
                                        elif char2 == "C":  # 右箭头
                                            return "right"
                                        elif char2 == "D":  # 左箭头
                                            return "left"

                            # 单独的ESC键
                            return "esc"
                        elif key == " ":  # 空格
                            return "space"
                        elif key == "\r" or key == "\n":  # 回车
                            return "enter"
                        elif key == "\x03":  # Ctrl+C
                            raise KeyboardInterrupt
                        elif key == "\x04":  # Ctrl+D
                            raise EOFError
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                else:
                    # 降级处理：使用标准输入
                    key = (
                        input("请输入命令 (u=上, d=下, s=选择, enter=确认, q=退出): ")
                        .strip()
                        .lower()
                    )
                    if key in ["u", "up"]:
                        return "up"
                    elif key in ["d", "down"]:
                        return "down"
                    elif key in ["s", "space", " "]:
                        return "space"
                    elif key in ["enter", ""]:
                        return "enter"
                    elif key in ["q", "quit", "esc"]:
                        return "esc"
        except (KeyboardInterrupt, EOFError):
            # 用户按Ctrl+C或Ctrl+D
            return "esc"
        except Exception:
            # 其他异常，返回None继续循环
            pass

        return None

    def _enable_ansi_on_windows(self):
        """在Windows上启用ANSI转义序列支持"""
        if sys.platform.startswith("win") and not self._ansi_enabled:
            try:
                import os
                import ctypes

                # 启用ANSI支持的多种方法
                os.system("color")

                # 使用更现代的Windows API方法
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

                self._ansi_enabled = True
            except (ImportError, OSError, AttributeError):
                # 如果失败，静默忽略
                pass

    def clear_screen(self):
        """清屏"""
        if sys.platform.startswith("win"):
            import os

            os.system("cls")
        else:
            print("\033[2J\033[H", end="")

    def move_cursor_up(self, lines):
        """向上移动光标"""
        if lines > 0:
            print(f"\033[{lines}A", end="")

    def clear_line(self):
        """清除当前行"""
        print("\033[K", end="")

    def hide_cursor(self):
        """隐藏光标"""
        print("\033[?25l", end="")

    def show_cursor(self):
        """显示光标"""
        print("\033[?25h", end="")

    def _format_menu_item(
        self, i: int, key: str, desc: str, max_width: int = 80
    ) -> str:
        """格式化菜单项"""
        # 当前选项高亮
        if i == self.current_index:
            prefix = "\033[1;36m>\033[0m"  # 青色高亮
        else:
            prefix = " "

        # 选中状态
        if key in self.selected_items:
            checkbox = "\033[1;32m[✓]\033[0m"  # 绿色选中
        else:
            checkbox = "[ ]"

        # 截断过长的描述
        if len(desc) > max_width - 10:
            desc = desc[: max_width - 13] + "..."

        return f"{prefix} {checkbox} {desc}"

    def show_menu(
        self, title: str, items: List[Tuple[str, str]], selected_items: List[str] = None
    ) -> List[str]:
        """
        显示交互式多选菜单

        Args:
            title: 菜单标题
            items: 选项列表，每个元素为 (key, description) 元组
            selected_items: 预选项目的key列表

        Returns:
            选中项目的key列表
        """
        if not items:
            return []

        # 启用ANSI支持和隐藏光标
        self._enable_ansi_on_windows()
        self.hide_cursor()

        try:
            if selected_items:
                self.selected_items = set(selected_items)
            else:
                self.selected_items = set()

            self.current_index = 0
            first_render = True

            while True:
                if first_render:
                    # 首次渲染，清屏并显示完整界面
                    self.clear_screen()

                    # 显示标题
                    print(f"\n\033[1;34m{title}\033[0m")  # 蓝色标题
                    print("=" * len(title))
                    print()

                    # 显示选项
                    for i, (key, desc) in enumerate(items):
                        print(self._format_menu_item(i, key, desc))

                    print()
                    print("\033[2m操作说明:\033[0m")  # 暗色操作说明
                    print("  \033[33m↑/↓\033[0m  : 上下移动")
                    print("  \033[33m空格\033[0m  : 选择/取消选择")
                    print("  \033[33m回车\033[0m  : 确认选择")
                    print("  \033[33mESC\033[0m   : 取消")

                    first_render = False
                else:
                    # 后续更新，只重绘菜单项部分
                    # 移动光标到菜单项开始位置
                    self.move_cursor_up(len(items) + 6)  # 菜单项 + 空行 + 操作说明

                    # 重新绘制菜单项
                    for i, (key, desc) in enumerate(items):
                        self.clear_line()
                        print(self._format_menu_item(i, key, desc))

                    # 移动光标回到底部
                    for _ in range(6):  # 空行 + 操作说明
                        print()

                # 刷新输出
                sys.stdout.flush()

                # 获取用户输入
                key = self.get_key()

                # 处理无效输入
                if key is None:
                    continue

                if key == "up":
                    self.current_index = (self.current_index - 1) % len(items)
                elif key == "down":
                    self.current_index = (self.current_index + 1) % len(items)
                elif key == "space":
                    current_key = items[self.current_index][0]
                    if current_key in self.selected_items:
                        self.selected_items.remove(current_key)
                    else:
                        self.selected_items.add(current_key)
                elif key == "enter":
                    return list(self.selected_items)
                elif key == "esc":
                    return []
        finally:
            # 恢复光标显示
            self.show_cursor()

    def show_single_choice_menu(
        self, title: str, items: List[Tuple[str, str]], default_key: str = None
    ) -> str:
        """
        显示交互式单选菜单

        Args:
            title: 菜单标题
            items: 选项列表，每个元素为 (key, description) 元组
            default_key: 默认选项的key

        Returns:
            选中项目的key，如果取消则返回None
        """
        # 设置默认选项的索引
        if default_key:
            for i, (key, _) in enumerate(items):
                if key == default_key:
                    self.current_index = i
                    break
        else:
            self.current_index = 0

        while True:
            self.clear_screen()

            # 显示标题
            print(f"\n{title}")
            print("=" * len(title))
            print()

            # 显示选项
            for i, (key, desc) in enumerate(items):
                # 当前选项高亮
                if i == self.current_index:
                    prefix = ">"
                    print(f"{prefix} ● {desc}")
                else:
                    prefix = " "
                    print(f"{prefix} ○ {desc}")

            print()
            print("操作说明:")
            print("  ↑/↓  : 上下移动")
            print("  回车  : 确认选择")
            print("  ESC   : 取消")

            # 获取用户输入
            key = self.get_key()

            if key == "up":
                self.current_index = (self.current_index - 1) % len(items)
            elif key == "down":
                self.current_index = (self.current_index + 1) % len(items)
            elif key == "enter":
                return items[self.current_index][0]
            elif key == "esc":
                return None
