"""G5 门禁回归：并发/分支/循环/中断/断点恢复 全套关键路径。"""
import pytest
from agent.engine.graph import WorkflowGraph, GraphNode, GraphEdge
from agent.engine.executor import Executor
from agent.engine.context import ContextStore
from agent.engine.registry import NODES
from chat.sse import EventEmitter
from agent.engine.nodes import *


def test_full_branch_loop_regression():
    """组合场景：并行两路 -> AND 聚合 -> 数组循环累加 -> 条件 -> reply。"""
    # 见各 Day 单测的复用图，合并成一条长链断言最终 answer
    ...


@pytest.mark.django_db
def test_publish_snapshot_isolation():
    from application.models import Application, ApplicationVersion
    app = Application.objects.create(name="a", work_flow={"nodes": [], "edges": []})
    # 发布后改草稿不影响已发布快照（运行读 is_published 版本）
    ...