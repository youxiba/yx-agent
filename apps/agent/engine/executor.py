# coding=utf-8
"""Executor V1：线性最小引擎。仅支持单后继串行（无分支/并发/循环），
负责事件发送（node_start/node_end）与 NodeResult 回写。D5 重写为并发版 V2。"""
from __future__ import annotations

from chat.sse import SSEEvent, EventEmitter, EVT_NODE_START, EVT_NODE_END
from agent.engine.errors import WorkflowEngineError
from agent.engine.graph import WorkflowGraph
from agent.engine.registry import NODES
from agent.engine.node import NodeContext, NodeResult


class Executor:
    def __init__(self, graph: WorkflowGraph) -> None:
        self.graph = graph

    def run(self, start_id: str, ctx: NodeContext, emitter: EventEmitter) -> None:
        """线性推进：从 start 沿单后继链执行直到没有后继。"""
        node_id = start_id
        visited: set[str] = set()
        while node_id is not None:
            if node_id in visited:
                raise WorkflowEngineError(f"检测到回环：节点 {node_id} 重复执行")
            visited.add(node_id)
            node = self.graph.get_node(node_id)
            inst = NODES.create(node.node_type, ctx.mode, node.config)
            inst.validate(node.config)
            emitter.emit(SSEEvent(EVT_NODE_START, node_id=node_id, node_type=node.node_type))
            result: NodeResult = inst.execute(ctx.fork(node_id, node.config))
            ctx.store.write_result(node_id, node.name, result.node_vars, result.global_vars)
            emitter.emit(SSEEvent(EVT_NODE_END, node_id=node_id, node_status="SUCCESS"))
            nxt = self.graph.successors(node_id)
            node_id = nxt[0] if nxt else None