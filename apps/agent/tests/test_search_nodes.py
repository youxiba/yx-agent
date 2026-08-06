# tests/test_search_nodes.py
import pytest
from agent.engine.graph import WorkflowGraph, GraphNode, GraphEdge
from agent.engine.executor import Executor
from agent.engine.context import ContextStore
from agent.engine.registry import NODES
from agent.tests.util import _mk_ctx
from chat.sse import EventEmitter
from agent.engine.nodes import *


class _Hit:
    def __init__(self, content, title, sim):
        self.content, self.title, self.similarity = content, title, sim
    def to_dict(self): return {"content": self.content, "title": self.title, "similarity": self.similarity}


class FakeVectorStore:
    def query(self, query_text, knowledge_ids, mode, top_n, similarity, model):
        assert query_text == "怎么部署"
        return [_Hit("部署方式A", "A", 0.9), _Hit("部署方式B", "B", 0.8)]
    def query_document(self, q, doc_ids, top_n, model):
        return [_Hit("文档内容", "doc", 0.7)]


class FakeReranker:
    def rerank(self, query, texts, top_n):
        return sorted(range(len(texts)), key=lambda i: len(texts[i]), reverse=True)[:top_n]


def test_search_knowledge_returns_paragraphs():
    g = WorkflowGraph()
    g.add_node(GraphNode("s", "start-node", "开始"))
    g.add_node(GraphNode("k", "search-knowledge-node", "知识库检索",
                         config={"knowledge_ids": ["k1"], "top_n": 2}))
    g.add_node(GraphNode("r", "reply-node", "回复", config={"content": "{{ 知识库检索.paragraph_list.0.content }}"}))
    g.add_edge(GraphEdge("s", "k")); g.add_edge(GraphEdge("k", "r"))
    store = ContextStore(); store.chat_vars["question"] = "怎么部署"
    em = EventEmitter()
    services = {"vector_store": FakeVectorStore(), "embedding_model": None}
    Executor(g).run(_mk_ctx(store, em, services=services), em, "s")
    assert store.resolve("global.answer") == "部署方式A"