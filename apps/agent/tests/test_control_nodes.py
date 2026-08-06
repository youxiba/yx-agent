import pytest
from agent.engine.graph import WorkflowGraph, GraphNode, GraphEdge
from agent.engine.executor import Executor
from agent.engine.context import ContextStore
from agent.engine.registry import NODES
from agent.tests.util import _mk_ctx
from chat.sse import EventEmitter
from agent.engine.nodes import *


class FakeModel:
    def invoke(self, messages):
        class _R:
            text = "MaxKB 支持哪些部署方式？"
        return _R()


class FakeGateway:
    def get_model(self, model_id): return FakeModel()


def test_start_reply_pipeline():
    g = WorkflowGraph()
    g.add_node(GraphNode("s", "start-node", "开始",
                         config={"global_variables": [{"variable": "company", "value": "MaxKB"}]}))
    g.add_node(GraphNode("r", "reply-node", "回复", config={"content": "欢迎使用{{ company }}"}))
    g.add_edge(GraphEdge("s", "r"))
    store = ContextStore(); em = EventEmitter()
    Executor(g).run(_mk_ctx(store, em, services={"gateway": FakeGateway()}), em, "s")
    assert store.resolve("global.answer") == "欢迎使用MaxKB"


def test_question_node_rewrites():
    g = WorkflowGraph()
    g.add_node(GraphNode("s", "start-node", "开始"))
    g.add_node(GraphNode("q", "question-node", "改写", config={"model_id": "m1"}))
    g.add_node(GraphNode("r", "reply-node", "回复", config={"content": "问题：{{ question }}"}))
    g.add_edge(GraphEdge("s", "q")); g.add_edge(GraphEdge("q", "r"))
    store = ContextStore(); store.chat_vars["question"] = "怎么部署"
    em = EventEmitter()
    Executor(g).run(_mk_ctx(store, em, services={"gateway": FakeGateway()}), em, "s")
    assert "MaxKB 支持哪些部署方式" in store.resolve("global.answer")