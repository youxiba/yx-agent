import time
import pytest
from agent.engine.graph import WorkflowGraph, GraphNode, GraphEdge
from agent.engine.node import BaseNode, NodeResult, NodeContext
from agent.engine.registry import NODES
from agent.engine.executor import Executor
from agent.engine.context import ContextStore
from chat.sse import EventEmitter
from agent.tests.util import _mk_ctx


class MinStartNode(BaseNode):
    node_type = "start-node"
    workflow_modes = ("application",)
    def execute(self, ctx): return NodeResult()


class SleepNode(BaseNode):
    node_type = "test-sleep-node"
    workflow_modes = ("application",)

    def __init__(self, config): super().__init__(config)
    def execute(self, ctx):
        time.sleep(0.05)
        return NodeResult(node_vars={"n": ctx.config.get("n", 0)})


def setup_module():
    NODES.register(MinStartNode)
    NODES.register(SleepNode)


def _fork_join_graph() -> WorkflowGraph:
    g = WorkflowGraph()
    for nid in ("s", "a", "b", "m"):
        g.add_node(GraphNode(node_id=nid, node_type="start-node", name=nid))
    g.nodes["a"].node_type = "test-sleep-node"
    g.nodes["b"].node_type = "test-sleep-node"
    g.nodes["m"].node_type = "test-sleep-node"
    g.nodes["m"].config = {"join_mode": "AND"}     # AND 合并
    g.add_edge(GraphEdge("s", "a")); g.add_edge(GraphEdge("s", "b"))
    g.add_edge(GraphEdge("a", "m")); g.add_edge(GraphEdge("b", "m"))
    return g


def test_parallel_fork_runs_both():
    g = _fork_join_graph()
    store = ContextStore()
    em = EventEmitter()
    Executor(g).run(_mk_ctx(store, em), em, start_id="s")
    # 节点名 == id；a/b 并发执行，m 是 AND 合并（requires_all）必须等 a、b 都 done
    assert {"s", "a", "b", "m"} <= set(store.node_vars)
    assert store.node_vars["m"]["n"] == 0


def test_parallel_fork_idempotent():
    """重复运行结果一致（并发竞态冒烟）。"""
    for _ in range(5):
        g = _fork_join_graph()
        store = ContextStore()
        em = EventEmitter()
        Executor(g).run(_mk_ctx(store, em), em, start_id="s")
        assert set(store.node_vars) == {"s", "a", "b", "m"}