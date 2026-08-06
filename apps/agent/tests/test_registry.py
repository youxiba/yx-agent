import pytest
from agent.engine.node import BaseNode, NodeResult, NodeContext
from agent.engine.registry import NodeRegistry


class PingNode(BaseNode):
    node_type = "ping-node"
    workflow_modes = ("application",)

    def execute(self, ctx: NodeContext) -> NodeResult:
        return NodeResult(node_vars={"pong": ctx.config.get("msg", "pong")})


def test_register_and_create():
    r = NodeRegistry()
    r.register(PingNode)
    assert r.has("ping-node", "application")
    assert not r.has("ping-node", "tool")
    node = r.create("ping-node", "application", {"msg": "hi"})
    assert isinstance(node, PingNode)


def test_create_missing_raises():
    r = NodeRegistry()
    with pytest.raises(KeyError):
        r.create("nope", "application", {})


def test_list_types():
    r = NodeRegistry()
    r.register(PingNode)
    assert "ping-node" in r.list_types("application")