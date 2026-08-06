# coding=utf-8
"""引擎顶层入口：run_workflow 供 chat 视图/测试/触发器复用。"""
from __future__ import annotations

from chat.sse import SSEEvent, EventEmitter, EVT_MESSAGE_END
from agent.engine.context import ContextStore
from agent.engine.executor import Executor
from agent.engine.graph import WorkflowGraph
from agent.engine.node import NodeContext


def run_workflow(graph: WorkflowGraph, *, mode: str = "application", inputs: dict | None = None,
                 emitter: EventEmitter | None = None, services: dict | None = None) -> ContextStore:
    """顶层入口：建 ContextStore、seed chat 变量、跑 Executor、收尾 message_end。"""
    store = ContextStore()
    store.chat_vars.update(inputs or {})
    services = services or {}
    emitter = emitter or EventEmitter()
    ctx = NodeContext(store=store, emitter=emitter, mode=mode, node_id="", config={},
                      services=services)
    Executor(graph).run(graph.get_start(), ctx, emitter)
    emitter.emit(SSEEvent(EVT_MESSAGE_END, is_end=True,
                          answer_text=store.global_vars.get("answer", "")))
    return store