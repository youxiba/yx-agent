# coding=utf-8
"""ai-chat-node：LLM 多轮对话（走 ModelGateway + SSE 流式）。"""
from __future__ import annotations
from chat.sse import SSEEvent, EVT_CONTENT_DELTA
from agent.engine.node import BaseNode, NodeResult, NodeContext


class AiChatNode(BaseNode):
    node_type = "ai-chat-node"
    workflow_modes = ("application", "knowledge", "tool")

    def validate(self, config: dict) -> None:
        assert config.get("model_id"), "ai-chat 节点必须指定 model_id"

    def execute(self, ctx: NodeContext) -> NodeResult:
        cfg = ctx.config
        gateway = ctx.get("gateway")
        model = gateway.get_model(cfg["model_id"])

        system = ctx.store.render(cfg.get("system", "你是智能助手。"))
        user_prompt = ctx.store.render(cfg.get("prompt", "{{ chat.question }}"))
        # 知识库上下文注入：前序检索节点输出 paragraph_list 拼接进 prompt
        if cfg.get("include_knowledge"):
            paras = ctx.get_field(cfg.get("knowledge_ref", "知识库检索.paragraph_list")) or []
            context = "\n".join(p.get("content", "") for p in paras)
            user_prompt = f"以下为参考资料，请据此回答：\n{context}\n\n{user_prompt}"

        history = ctx.get_field("chat.chat_history") or []
        messages = [{"role": "system", "content": system}]
        messages += [{"role": h.get("role"), "content": h.get("content")} for h in history]
        messages.append({"role": "user", "content": user_prompt})

        answer, usage = "", {}
        for chunk in model.stream(messages):           # 流式增量
            text = chunk.text or ""
            if text:
                answer += text
                ctx.emitter.emit(SSEEvent(EVT_CONTENT_DELTA, node_id=ctx.node_id, content=text,
                                          reasoning_content=getattr(chunk, "reasoning_content", "") or ""))
        if hasattr(model, "last_usage"):
            usage = model.last_usage
        return NodeResult(node_vars={"answer": answer, "usage": usage},
                          global_vars={"answer": answer, "usage": usage})