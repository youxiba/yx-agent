# tests/test_form_interrupt.py
import pytest
from agent.models import Application, WorkflowExecution
from agent.engine.graph import WorkflowGraph, GraphNode, GraphEdge
from agent.engine.executor import Executor
from agent.engine.context import ContextStore
from agent.engine.node import BaseNode, NodeResult, NodeContext
from agent.engine.registry import NODES
from chat.sse import EventEmitter
from agent.engine.nodes import *


class EchoNode(BaseNode):
    node_type = "test-echo-node"
    workflow_modes = ("application",)
    def execute(self, ctx):
        return NodeResult(global_vars={"after": "续跑完成"})


@pytest.mark.django_db
def test_form_interrupt_and_resume():
    app = Application.objects.create(name="表单应用", work_flow={})
    g = WorkflowGraph()
    g.add_node(GraphNode("s", "start-node", "开始"))
    g.add_node(GraphNode("f", "form-node", "填表", config={"fields": [{"name": "age",
                                                                       "label": "年龄", "type": "number"}]}))
    g.add_node(GraphNode("e", "test-echo-node", "续跑"))
    g.add_edge(GraphEdge("s", "f")); g.add_edge(GraphEdge("f", "e"))
    app.work_flow = g.to_json(); app.save()

    from agent.services import ApplicationWorkflowService
    svc = ApplicationWorkflowService({"graph": g})
    em = EventEmitter()
    store = svc.execute(app, {"question": "开始"}, em)
    # 中断后未继续：无 answer，execution 落 WAIT_USER
    exec_row = WorkflowExecution.objects.filter(application=app).first()
    assert exec_row.status == WorkflowExecution.Status.WAIT_USER
    # 恢复
    em2 = EventEmitter()
    store2 = svc.resume(str(exec_row.id), {"age": 18}, em2)
    assert store2.resolve("global.after") == "续跑完成"
    assert store2.resolve("global.form_data") == {"age": 18}