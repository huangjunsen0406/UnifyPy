#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
事件总线：支持生命周期事件的订阅与触发，按优先级调用处理器。
"""

from typing import Any, Callable, DefaultDict, Dict, List, Tuple
from collections import defaultdict


Handler = Callable[[Any], None]


class EventBus:
    """简单的事件总线，支持优先级和异常隔离。"""

    def __init__(self):
        self._subscribers: DefaultDict[str, List[Tuple[int, Handler]]] = defaultdict(list)

    def subscribe(self, event: str, handler: Handler, priority: int = 100) -> None:
        self._subscribers[event].append((priority, handler))
        # 按优先级升序排序（数值越小越先执行）
        self._subscribers[event].sort(key=lambda x: x[0])

    def emit(self, event: str, context: Any) -> None:
        handlers = self._subscribers.get(event, [])
        for _, handler in handlers:
            try:
                handler(context)
            except Exception as e:
                # 将异常记录到上下文，交由引擎统一处理
                if hasattr(context, "errors") and isinstance(context.errors, list):
                    context.errors.append((event, e))
                else:
                    # 兜底：直接抛出
                    raise

