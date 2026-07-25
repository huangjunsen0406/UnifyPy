#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
事件总线：支持生命周期事件的订阅与触发，按优先级调用处理器。
"""

from typing import Any, Callable, DefaultDict, List, Tuple
from collections import defaultdict


Handler = Callable[[Any], None]


class EventBus:
    """简单的事件总线，支持优先级。

    Fail-fast within an event: if a handler raises, the error is recorded on
    ``context.errors`` and remaining handlers for that event are **not** called.
    """

    def __init__(self):
        self._subscribers: DefaultDict[str, List[Tuple[int, Handler]]] = defaultdict(list)

    def subscribe(self, event: str, handler: Handler, priority: int = 100) -> None:
        self._subscribers[event].append((priority, handler))
        # 按优先级升序排序（数值越小越先执行）
        self._subscribers[event].sort(key=lambda x: x[0])

    def emit(self, event: str, context: Any) -> None:
        """Emit an event to subscribers in priority order.

        On handler exception, record ``(event, exc)`` on ``context.errors``
        (when available) and stop invoking remaining handlers for this event.
        """
        handlers = self._subscribers.get(event, [])
        for _, handler in handlers:
            try:
                handler(context)
            except Exception as e:
                # 将异常记录到上下文，交由引擎统一处理；同事件后续 handler 不再调用
                if hasattr(context, "errors") and isinstance(context.errors, list):
                    context.errors.append((event, e))
                    break
                # 兜底：直接抛出
                raise

