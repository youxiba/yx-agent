# coding=utf-8
"""引擎顶层入口：run_workflow 供 chat 视图/测试/触发器复用。"""
from __future__ import annotations

from chat.sse import SSEEvent, EventEmitter, EVT_MESSAGE_END
from agent.engine.context import ContextStore
from agent.engine.executor import Executor
from agent.engine.graph import WorkflowGraph
from agent.engine.node import NodeContext


def run_workflow(graph, *, mode="application", inputs=None, emitter=None, services=None):
    store = ContextStore()
    store.chat_vars.update(inputs or {})
    services = dict(services or {})
    services.setdefault("graph", graph)
    executor = Executor(graph)
    services.setdefault("executor", executor)          # LoopNode 经 ctx.get('executor') 调用 run_subgraph
    emitter = emitter or EventEmitter()
    ctx = NodeContext(store=store, emitter=emitter, mode=mode, node_id="", config={},
                      services=services)
    executor.run(ctx, emitter, start_id=graph.get_start())
    emitter.emit(SSEEvent(EVT_MESSAGE_END, is_end=True,
                          answer_text=store.global_vars.get("answer", "")))
    emitter.close()   # 结束哨兵，否则消费者（stream/events）阻塞等待
    return store