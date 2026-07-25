#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Unit tests for EventBus fail-fast behavior."""

from types import SimpleNamespace

from unifypy.core.event_bus import EventBus


def test_second_handler_not_called_after_first_raises():
    bus = EventBus()
    called = []

    def first(_ctx):
        called.append("first")
        raise RuntimeError("boom")

    def second(_ctx):
        called.append("second")

    bus.subscribe("test", first, priority=10)
    bus.subscribe("test", second, priority=20)

    ctx = SimpleNamespace(errors=[])
    bus.emit("test", ctx)

    assert called == ["first"]
    assert len(ctx.errors) == 1
    assert ctx.errors[0][0] == "test"
    assert isinstance(ctx.errors[0][1], RuntimeError)
    assert str(ctx.errors[0][1]) == "boom"


def test_all_handlers_run_when_none_raise():
    bus = EventBus()
    called = []

    bus.subscribe("ok", lambda c: called.append("a"), priority=10)
    bus.subscribe("ok", lambda c: called.append("b"), priority=20)

    ctx = SimpleNamespace(errors=[])
    bus.emit("ok", ctx)

    assert called == ["a", "b"]
    assert ctx.errors == []


def test_priority_order_before_fail():
    bus = EventBus()
    called = []

    def low(_ctx):
        called.append("low")

    def mid(_ctx):
        called.append("mid")
        raise ValueError("stop")

    def high(_ctx):
        called.append("high")

    bus.subscribe("ev", high, priority=30)
    bus.subscribe("ev", low, priority=10)
    bus.subscribe("ev", mid, priority=20)

    ctx = SimpleNamespace(errors=[])
    bus.emit("ev", ctx)

    assert called == ["low", "mid"]
    assert len(ctx.errors) == 1
    assert isinstance(ctx.errors[0][1], ValueError)
