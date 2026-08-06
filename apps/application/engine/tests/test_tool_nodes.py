# coding=utf-8
"""tool-node / tool-lib-node 与引擎集成测试"""
import pytest
from apps.application.engine.node import NodeContext, NodeResult
from apps.application.engine.nodes.tool_node import ToolNode
from apps.application.engine.nodes.tool_lib_node import ToolLibNode
from apps.tool.models import Tool, ToolRecord


@pytest.mark.django_db
def test_tool_node_executes_code():
    ctx = NodeContext(node_id="n1", config={"code": "_maxkb_returns(s=_inputs['a']+_inputs['b'])",
                                            "inputs": {"a": "global.a", "b": "global.b"}},
                      store=_store({"global.a": 1, "global.b": 2}), chat_id=None, emitter=None)
    result = ToolNode().execute(ctx)
    assert result.node_vars["output"] == {"s": 3}


@pytest.mark.django_db
def test_tool_lib_node_only_published():
    Tool.objects.create(name="t1", label="T", code="_maxkb_returns(v=_inputs['x'])", status=Tool.Status.DRAFT,
                        creator_id=1, input_schema={"type": "object"})
    ctx = NodeContext(node_id="n1", config={"tool_name": "t1", "inputs": {"x": "global.x"}},
                      store=_store({"global.x": 5}), chat_id=None, emitter=None)
    with pytest.raises(Exception):        # DRAFT 不可被引用 → 404 异常
        ToolLibNode().execute(ctx)


def _store(vals):
    from apps.application.engine.context import ContextStore
    s = ContextStore(); s.global_vars = vals; return s