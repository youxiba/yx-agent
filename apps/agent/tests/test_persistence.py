import pytest
from agent.models import Application, WorkflowExecution
from agent.engine.graph import WorkflowGraph, GraphNode, GraphEdge
from agent.engine.persistence import ExecutionPersistence
from agent.engine.context import ContextStore
from agent.engine.node import BaseNode, NodeResult, NodeContext
from agent.engine.registry import NODES
from agent.engine.executor import Executor
from chat.sse import EventEmitter
from agent.tests.util import _mk_ctx
from agent.engine.nodes import *


class MinStartNode(BaseNode):           # D9 前兜底：start-node 还未在 nodes 包注册
    node_type = "start-node"
    workflow_modes = ("application",)
    def execute(self, ctx): return NodeResult()


class StepNode(BaseNode):
    node_type = "test-step-node"
    workflow_modes = ("application",)
    def __init__(self, config): super().__init__(config); self.seq = config.get("seq")
    def execute(self, ctx):
        s = ctx.store.global_vars.get("steps", 0) + self.seq
        return NodeResult(global_vars={"steps": s})


def setup_module():
    NODES.register(MinStartNode)


@pytest.mark.django_db
def test_interrupt_then_resume_matches_full_run():
    NODES.register(StepNode)
    app = Application.objects.create(name="app", work_flow={})

    def build():
        g = WorkflowGraph()
        g.add_node(GraphNode("s", "start-node", "开始"))
        for i, seq in enumerate([1, 2, 3], start=1):
            g.add_node(GraphNode(f"n{i}", "test-step-node", f"步{i}", config={"seq": seq}))
        g.add_edge(GraphEdge("s", "n1")); g.add_edge(GraphEdge("n1", "n2"))
        g.add_edge(GraphEdge("n2", "n3"))
        return g

    # 完整跑一次
    full = ContextStore(); Executor(build()).run(_mk_ctx(full, EventEmitter()), EventEmitter(), "s")
    # 中断：只跑 n1、n2 后 snapshot（模拟 n3 前中断）
    partial = ContextStore(); partial.global_vars["steps"] = 3   # 等价 n1+n2 后的状态
    pers = ExecutionPersistence(app)
    exec_id = pers.snapshot(status=WorkflowExecution.Status.WAIT_USER,
                            done_nodes={"s", "n1", "n2"}, next_node="n3",
                            store=partial, details={"at": "n3"})
    # 恢复 + 续跑
    graph, done, store = pers.restore(exec_id)
    em = EventEmitter()
    Executor(graph).run(_mk_ctx(store, em), em, start_id="n3", pre_done=done)
    assert store.resolve("global.steps") == full.resolve("global.steps")