#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
进度回调工厂
统一创建和管理进度回调函数
"""

from typing import Callable


class ProgressCallbackFactory:
    """
    进度回调函数工厂类.
    用于创建统一的进度回调函数，避免重复代码.
    """

    @staticmethod
    def create_callback(
        progress_manager,
        verbose: bool = False
    ) -> Callable[[str, str], None]:
        """
        创建进度回调函数.

        Args:
            progress_manager: 进度管理器实例
            verbose: 是否启用详细模式

        Returns:
            Callable: 进度回调函数 callback(message, level='info')
        """
        def progress_callback(message: str, level: str = 'info'):
            """
            处理进度消息的回调函数.

            Args:
                message: 消息内容
                level: 消息级别 ('info', 'success', 'warning', 'error')
            """
            # 非 verbose 模式下不显示详细消息
            if not verbose:
                return

            # 根据级别添加emoji前缀并调用对应的方法
            if level == 'success':
                progress_manager.info(f"✅ {message}")
            elif level == 'warning':
                progress_manager.warning(f"⚠️ {message}")
            elif level == 'error':
                progress_manager.warning(f"❌ {message}")
            else:  # info
                progress_manager.info(f"📋 {message}")

        return progress_callback

    # 注意：create_summary_callback 未被使用，已移除以简化接口
