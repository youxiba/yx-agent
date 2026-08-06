import pytest
from agent.engine.graph import WorkflowGraph, GraphNode, GraphEdge
from agent.engine.executor import Executor
from agent.engine.context import ContextStore
from agent.engine.node import BaseNode, NodeResult, NodeContext
from agent.engine.registry import NODES
from chat.sse import EventEmitter
from agent.tests.util import _mk_ctx
from agent.engine.nodes import *


class MinStartNode(BaseNode):           # D9 前兜底：start-node 还未在 nodes 包注册
    node_type = "start-node"
    workflow_modes = ("application",)
    def execute(self, ctx): return NodeResult()


class AccumNode(BaseNode):
    node_type = "test-accum-node"
    workflow_modes = ("application",)
    def execute(self, ctx):
        total = ctx.store.global_vars.get("sum", 0) + (ctx.get_field("loop.item") or 0)
        return NodeResult(global_vars={"sum": total})


def setup_module():
    NODES.register(MinStartNode)


def build_array_loop_graph() -> WorkflowGraph:
    g = WorkflowGraph()
    g.add_node(GraphNode(node_id="s", node_type="start-node", name="开始"))
    g.add_node(GraphNode(node_id="L", node_type="loop-node", name="循环",
                         config={"mode": "ARRAY", "loop_list": "global.nums"}))
    g.add_node(GraphNode(node_id="ls", node_type="loop-start-node", name="体入口",
                         config={}, loop_container="L"))
    g.add_node(GraphNode(node_id="acc", node_type="test-accum-node", name="累加",
                         config={}, loop_container="L"))
    g.add_node(GraphNode(node_id="r", node_type="start-node", name="结束"))  # 复用兜底 start
    g.add_edge(GraphEdge("s", "L")); g.add_edge(GraphEdge("L", "ls"))
    g.add_edge(GraphEdge("ls", "acc")); g.add_edge(GraphEdge("acc", "L"))    # 体末回边
    g.add_edge(GraphEdge("L", "r"))
    return g


def test_array_loop_accumulate():
    NODES.register(AccumNode)
    g = build_array_loop_graph()
    store = ContextStore(); store.global_vars["nums"] = [1, 2, 3]
    em = EventEmitter()
    exe = Executor(g)
    ctx = _mk_ctx(store, em, services={"graph": g, "executor": exe})   # LoopNode 需要 graph + executor
    exe.run(ctx, em, start_id="s")
    assert store.resolve("global.sum") == 6
    assert store.resolve("global.nums") == [1, 2, 3]