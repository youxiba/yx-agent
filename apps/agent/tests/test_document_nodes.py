import pytest
from agent.engine.graph import WorkflowGraph, GraphNode, GraphEdge
from agent.engine.executor import Executor
from agent.engine.context import ContextStore
from agent.engine.registry import NODES
from agent.tests.util import _mk_ctx
from chat.sse import EventEmitter
from agent.engine.nodes import *
from agent.engine.errors import WorkflowEngineError


class FakeKnowledgeService:
    def extract_document_content(self, doc_id): return "文档正文内容..."
    def batch_write_paragraphs(self, knowledge_id, paragraphs, source):
        assert knowledge_id == "kb1"
        return len(paragraphs)


class FakeSplitter:
    def split(self, content, limit, pattern): return [content[:limit]] * 2


def test_extract_split_write_chain():
    g = WorkflowGraph()
    g.add_node(GraphNode("s", "start-node", "开始"))
    g.add_node(GraphNode("e", "document-extract-node", "提取", config={"document_id": "d1"}))
    g.add_node(GraphNode("sp", "document-split-node", "切分",
                         config={"content_ref": "提取.content", "chunk_size": 10}))
    g.add_node(GraphNode("w", "knowledge-write-node", "入库",
                         config={"knowledge_id": "kb1", "paragraph_ref": "切分.paragraph_list"}))
    g.add_edge(GraphEdge("s", "e")); g.add_edge(GraphEdge("e", "sp")); g.add_edge(GraphEdge("sp", "w"))
    store = ContextStore(); em = EventEmitter()
    services = {"knowledge_service": FakeKnowledgeService(), "splitter": FakeSplitter()}
    Executor(g).run(_mk_ctx(store, em, services=services), em, "s")
    assert store.resolve("入库.written") == 2


def test_knowledge_write_empty_raises():
    g = WorkflowGraph()
    g.add_node(GraphNode("s", "start-node", "开始"))
    g.add_node(GraphNode("w", "knowledge-write-node", "入库",
                         config={"knowledge_id": "kb1", "paragraph_ref": "切分.paragraph_list"}))
    g.add_edge(GraphEdge("s", "w"))
    store = ContextStore(); em = EventEmitter()
    with pytest.raises(WorkflowEngineError):
        Executor(g).run(_mk_ctx(store, em, services={"knowledge_service": object(),
                                                     "splitter": object()}), em, "s")