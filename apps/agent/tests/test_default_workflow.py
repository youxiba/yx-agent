import pytest
from agent.default_workflow.templates import LANGS, load_template, build_graph
from agent.engine.executor import Executor
from agent.engine.context import ContextStore
from agent.engine.registry import NODES
from agent.engine.nodes import *
from chat.sse import EventEmitter


def test_all_langs_load_and_validate():
    for lang in LANGS:
        data = load_template(lang)
        assert data["language"] == lang
        g = build_graph(lang, knowledge_id="k1")
        g.validate()
        assert any(n.node_type == "search-knowledge-node" for n in g.nodes.values())


def test_bind_knowledge_id():
    g = build_graph("zh_CN", knowledge_id="kb-9")
    sk = next(n for n in g.nodes.values() if n.node_type == "search-knowledge-node")
    assert sk.config["knowledge_ids"] == ["kb-9"]


def test_template_condition_branch():
    g = build_graph("zh_CN")
    start = next(n for n in g.nodes.values() if n.node_type == "condition-node")
    assert len(g.out_edges(start.node_id)) == 2      # true/false 两分支