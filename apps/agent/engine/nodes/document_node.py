# coding=utf-8
"""文档类节点：document-extract / document-split / knowledge-write。"""
from __future__ import annotations
from agent.engine.node import BaseNode, NodeResult, NodeContext
from agent.engine.errors import WorkflowEngineError


class DocumentExtractNode(BaseNode):
    node_type = "document-extract-node"
    workflow_modes = ("application", "knowledge")

    def execute(self, ctx: NodeContext) -> NodeResult:
        doc_id = ctx.config.get("document_id")
        content = ctx.get("knowledge_service").extract_document_content(doc_id)
        return NodeResult(node_vars={"content": content})


class DocumentSplitNode(BaseNode):
    node_type = "document-split-node"
    workflow_modes = ("application", "knowledge")

    def execute(self, ctx: NodeContext) -> NodeResult:
        cfg = ctx.config
        content = ctx.get_field(cfg.get("content_ref", "文档提取.content")) or ""
        splitter = ctx.get("splitter")                  # Phase3 SplitModel 工厂
        chunks = splitter.split(content, limit=cfg.get("chunk_size", 1024),
                                pattern=cfg.get("pattern", ""))
        return NodeResult(node_vars={"paragraph_list": chunks})


class KnowledgeWriteNode(BaseNode):
    node_type = "knowledge-write-node"
    workflow_modes = ("application", "knowledge")

    def execute(self, ctx: NodeContext) -> NodeResult:
        cfg = ctx.config
        knowledge_id = cfg.get("knowledge_id")
        paragraphs = ctx.get_field(cfg.get("paragraph_ref", "文档切分.paragraph_list")) or []
        if not paragraphs:
            raise WorkflowEngineError("knowledge-write 无待写入段落")
        written = ctx.get("knowledge_service").batch_write_paragraphs(
            knowledge_id, paragraphs, source=cfg.get("source", "workflow"))
        return NodeResult(node_vars={"written": written})