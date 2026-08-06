# coding=utf-8
"""检索类节点：search-knowledge / search-document / reranker。"""
from __future__ import annotations
from agent.engine.node import BaseNode, NodeResult, NodeContext


class SearchKnowledgeNode(BaseNode):
    node_type = "search-knowledge-node"
    workflow_modes = ("application", "knowledge")

    def validate(self, config: dict) -> None:
        assert config.get("knowledge_ids") or config.get("knowledge_ref"), "knowledge_ids 必填"

    def execute(self, ctx: NodeContext) -> NodeResult:
        cfg = ctx.config
        vector_store = ctx.get("vector_store")
        embedding_model = ctx.get("embedding_model")
        k_ids = (ctx.get_field(cfg["knowledge_ref"]) if cfg.get("knowledge_ref")
                 else cfg.get("knowledge_ids", []))
        question = ctx.store.render(cfg.get("question", "{{ chat.question }}"))
        hits = vector_store.query(
            query_text=question, knowledge_ids=k_ids,
            mode=cfg.get("search_mode", "blend"),
            top_n=cfg.get("top_n", 3), similarity=cfg.get("similarity", 0.0),
            model=embedding_model,
        )
        paragraph_list = [h.to_dict() for h in hits]        # Hit -> dict（content/title/similarity）
        return NodeResult(node_vars={"paragraph_list": paragraph_list, "hit_list": paragraph_list})


class SearchDocumentNode(BaseNode):
    node_type = "search-document-node"
    workflow_modes = ("application", "knowledge")

    def execute(self, ctx: NodeContext) -> NodeResult:
        cfg = ctx.config
        vector_store = ctx.get("vector_store")
        embedding_model = ctx.get("embedding_model")
        doc_ids = cfg.get("document_ids", [])
        question = ctx.store.render(cfg.get("question", "{{ chat.question }}"))
        hits = vector_store.query_document(question, doc_ids, cfg.get("top_n", 5),
                                           embedding_model)
        return NodeResult(node_vars={"paragraph_list": [h.to_dict() for h in hits]})


class RerankerNode(BaseNode):
    node_type = "reranker-node"
    workflow_modes = ("application", "knowledge")

    def execute(self, ctx: NodeContext) -> NodeResult:
        cfg = ctx.config
        reranker = ctx.get("reranker_model")                # gateway 提供 reranker 模型
        paragraphs = ctx.get_field(cfg.get("paragraph_ref", "知识库检索.paragraph_list")) or []
        query = ctx.store.render(cfg.get("question", "{{ chat.question }}"))
        scored = reranker.rerank(query, [p["content"] for p in paragraphs],
                                 top_n=cfg.get("top_n", 5))
        out = []
        for i, s in scored:                                  # scored: [(index, score)]
            p = dict(paragraphs[i]); p["rerank_score"] = s
            out.append(p)
        return NodeResult(node_vars={"rerank_list": out}, global_vars={"rerank_list": out})