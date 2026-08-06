# coding=utf-8
"""application-node：调用子应用（复用 chat 应用执行链路，非递归自调用）。"""
from __future__ import annotations
from agent.engine.node import BaseNode, NodeResult, NodeContext


class ApplicationNode(BaseNode):
    node_type = "application-node"
    workflow_modes = ("application",)

    def execute(self, ctx: NodeContext) -> NodeResult:
        cfg = ctx.config
        app_service = ctx.get("application_service")
        question = ctx.store.render(cfg.get("question", "{{ chat.question }}"))
        answer = app_service.chat_sync(
            app_id=cfg["application_id"],
            question=question,
            history=ctx.get_field("chat.chat_history") or [],
        )
        return NodeResult(node_vars={"answer": answer}, global_vars={"answer": answer})