import json
import pytest
from chat.sse import EventEmitter, EVT_NODE_START, EVT_NODE_END, EVT_MESSAGE_END
from agent.engine import run_workflow
from agent.engine.node import BaseNode, NodeResult, NodeContext
from agent.engine.registry import NODES
from agent.engine.graph import WorkflowGraph, GraphNode, GraphEdge


# 注：start-node 正式实现见 D9。为 Day4 可独立跑，这里注册一个最小 StartNode 兜底。
class MinStartNode(BaseNode):
    node_type = "start-node"
    workflow_modes = ("application",)

    def execute(self, ctx: NodeContext) -> NodeResult:
        return NodeResult(global_vars=dict(ctx.config.get("global_variables", [])))


class AddOneNode(BaseNode):
    """测试节点：把输入字段 + 1 写到 node_vars。"""
    node_type = "test-addone-node"
    workflow_modes = ("application",)

    def execute(self, ctx: NodeContext) -> NodeResult:
        src = ctx.config.get("ref", "chat.x")
        val = ctx.get_field(src) or 0
        return NodeResult(node_vars={"out": val + 1}, global_vars={"x": val + 1})


def setup_module():
    NODES.register(MinStartNode)
    NODES.register(AddOneNode)


def test_linear_execution_and_events():
    g = WorkflowGraph()
    g.add_node(GraphNode(node_id="s", node_type="start-node", name="开始"))
    g.add_node(GraphNode(node_id="a", node_type="test-addone-node", name="加一",
                         config={"ref": "chat.x"}))
    g.add_node(GraphNode(node_id="r", node_type="test-addone-node", name="再加一",
                         config={"ref": "加一.out"}))
    g.add_edge(GraphEdge(source="s", target="a"))
    g.add_edge(GraphEdge(source="a", target="r"))

    em = EventEmitter()
    store = run_workflow(g, inputs={"x": 1}, emitter=em, services={})
    events = list(em.stream())
    assert store.resolve("global.x") == 3
    assert store.resolve("再加一.out") == 3
    types = [json.loads(e)["type"] for e in events]
    # s/a/r 三个节点：node_start + node_end 各 3 组，最后 message_end
    assert types == [EVT_NODE_START, EVT_NODE_END] * 3 + [EVT_MESSAGE_END]