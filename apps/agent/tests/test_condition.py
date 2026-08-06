import pytest
from agent.engine.graph import WorkflowGraph, GraphNode, GraphEdge
from agent.engine.executor import Executor
from agent.engine.context import ContextStore
from agent.engine.node import BaseNode, NodeResult, NodeContext
from agent.engine.registry import NODES
from chat.sse import EventEmitter
from agent.tests.util import _mk_ctx
from agent.engine.nodes import *        # 触发装配


class CaptureNode(BaseNode):
    node_type = "test-capture-node"
    workflow_modes = ("application",)
    def execute(self, ctx): return NodeResult(node_vars={"via": ctx.node_id})


def test_branch_routing_true():
    NODES.register(CaptureNode)
    g = WorkflowGraph()
    g.add_node(GraphNode(node_id="s", node_type="start-node", name="开始"))
    g.add_node(GraphNode(node_id="c", node_type="condition-node", name="条件",
                         config={"branches": [{"branch_id": "true",
                                               "conditions": [{"field": "global.x",
                                                               "comparator": "eq", "value": 1}]}],
                                 "default_branch_id": "false"}))
    g.add_node(GraphNode(node_id="T", node_type="test-capture-node", name="真"))
    g.add_node(GraphNode(node_id="F", node_type="test-capture-node", name="假"))
    g.add_edge(GraphEdge("s", "c"))
    g.add_edge(GraphEdge("c", "T", branch_id="true"))
    g.add_edge(GraphEdge("c", "F", branch_id="false"))

    store = ContextStore(); store.global_vars["x"] = 1
    em = EventEmitter()
    Executor(g).run(_mk_ctx(store, em), em, start_id="s")
    assert store.node_vars["真"]["via"] == "T" and "假" not in store.node_vars