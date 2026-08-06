# tests/test_variable_nodes.py
import pytest
from agent.engine.graph import WorkflowGraph, GraphNode, GraphEdge
from agent.engine.executor import Executor
from agent.engine.context import ContextStore
from agent.engine.node import BaseNode, NodeResult
from agent.engine.registry import NODES
from agent.tests.util import _mk_ctx
from chat.sse import EventEmitter
from agent.engine.nodes import *


class SplitNode(BaseNode):
    node_type = "test-split-node"
    workflow_modes = ("application",)
    def execute(self, ctx):
        return NodeResult(node_vars={"piece": ctx.config.get("v")})


def test_aggregation_joins_branches():
    g = WorkflowGraph()
    g.add_node(GraphNode("s", "start-node", "开始"))
    g.add_node(GraphNode("c", "condition-node", "条件",
                         config={"branches": [{"branch_id": "true",
                                               "conditions": [{"field": "global.x", "comparator": "eq",
                                                               "value": 1}]}],
                                 "default_branch_id": "false"}))
    g.add_node(GraphNode("A", "test-split-node", "A", config={"v": "a"}))
    g.add_node(GraphNode("B", "test-split-node", "B", config={"v": "b"}))
    g.add_node(GraphNode("agg", "aggregation-node", "聚合",
                         config={"join_mode": "AND", "source_refs": ["A.piece", "B.piece"]}))
    g.add_edge(GraphEdge("s", "c"))
    g.add_edge(GraphEdge("c", "A", branch_id="true"))
    g.add_edge(GraphEdge("c", "B", branch_id="false"))
    g.add_edge(GraphEdge("A", "agg")); g.add_edge(GraphEdge("B", "agg"))
    store = ContextStore(); store.global_vars["x"] = 1
    em = EventEmitter()
    Executor(g).run(_mk_ctx(store, em), em, "s")
    # 只走 true 分支，聚合只收 A；B 未激活不阻塞 AND 合并
    assert store.resolve("聚合.result_list") == ["a"]