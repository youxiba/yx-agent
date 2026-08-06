# coding=utf-8
"""默认模板加载：按语言返回模板 DAG，供『新建应用』一键导入。"""
from __future__ import annotations
import json
from pathlib import Path

from agent.engine.graph import WorkflowGraph

_TEMPLATE_DIR = Path(__file__).resolve().parent

LANGS = ("zh_CN", "en_US", "zh_Hant")


def load_template(lang: str) -> dict:
    if lang not in LANGS:
        lang = "zh_CN"
    with open(_TEMPLATE_DIR / f"default_workflow_{lang}.json", encoding="utf-8") as f:
        return json.load(f)


def build_graph(lang: str = "zh_CN", knowledge_id: str | None = None) -> WorkflowGraph:
    """加载模板并绑定知识库 id；返回可直接执行的图。"""
    data = load_template(lang)
    g = WorkflowGraph.from_json(data["work_flow"])
    if knowledge_id:
        for n in g.nodes.values():
            if n.node_type == "search-knowledge-node":
                n.config["knowledge_ids"] = [knowledge_id]
    g.validate()
    return g