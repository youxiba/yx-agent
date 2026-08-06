# coding=utf-8
"""reply-node：渲染引用/自定义内容，写 answer 并流式发出。"""
from __future__ import annotations
from chat.sse import SSEEvent, EVT_CONTENT_DELTA
from agent.engine.node import BaseNode, NodeResult, NodeContext


class ReplyNode(BaseNode):
    node_type = "reply-node"
    workflow_modes = ("application", "knowledge", "tool")

    def validate(self, config: dict) -> None:
        assert config.get("content"), "reply 内容不能为空"

    def execute(self, ctx: NodeContext) -> NodeResult:
        content = ctx.store.render(ctx.config.get("content", ""))
        ctx.emitter.emit(SSEEvent(EVT_CONTENT_DELTA, node_id=ctx.node_id, content=content))
        return NodeResult(node_vars={"answer": content}, global_vars={"answer": content})