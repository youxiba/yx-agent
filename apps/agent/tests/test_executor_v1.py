import json
import pytest
from chat.sse import EventEmitter, EVT_NODE_START, EVT_NODE_END, EVT_MESSAGE_END
from agent.engine import run_workflow
from agent.engine.node import BaseNode, NodeResult, NodeContext
from agent.engine.registry import NODES
from agent.engine.graph import WorkflowGraph, GraphNode, GraphEdge


class AddOneNode(BaseNode):
    """测试节点：把输入字段 + 1 写到 node_vars。"""
    node_type = "test-addone-node"
    workflow_modes = ("application",)

    def execute(self, ctx: NodeContext) -> NodeResult:
        src = ctx.config.get("ref", "chat.x")
        val = ctx.get_field(src) or 0
        return NodeResult(node_vars={"out": val + 1}, global_vars={"x": val + 1})


def setup_module():
    NODES.register(AddOneNode)   # start-node 用真实实现（nodes/__init__.py 已注册）


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
    types = [json.loads(e[6:])["type"] for e in events]   # 帧格式 data: {json}\n\n，剥前缀
    # s/a/r 三个节点：node_start + node_end 各 3 组，最后 message_end
    assert types == [EVT_NODE_START, EVT_NODE_END] * 3 + [EVT_MESSAGE_END]