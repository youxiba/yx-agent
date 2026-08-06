# tests/util.py：快捷构造 NodeContext，供后续各 Day 测试文件复用。
from __future__ import annotations

from chat.sse import EventEmitter
from agent.engine.context import ContextStore
from agent.engine.node import NodeContext


def _mk_ctx(store=None, emitter=None, services=None) -> NodeContext:
    return NodeContext(store=store or ContextStore(), emitter=emitter or EventEmitter(),
                       mode="application", node_id="", config={}, services=services or {})