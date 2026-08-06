# apps/chat/engine/v1/steps/chat_step.py
"""LLM 流式回答步骤：gateway.get_model().stream(messages) 逐块 emit content_delta。"""
from chat.sse import EVT_CONTENT_DELTA, EVT_MESSAGE_END, EVT_NODE_END, EVT_NODE_START, SSEEvent
from common.exceptions import AppApiException
from ..context import PipelineContext
from ..pipeline import IBaseStep


class ChatStep(IBaseStep):
    step_type = "ai_chat"

    def __init__(self, gateway):
        self.gateway = gateway                   # model_platform.ModelGateway 实例

    def valid_args(self, ctx: PipelineContext) -> None:
        if ctx.directly_return:                  # 直接返回：跳过 LLM 也不校验模型
            return
        model_id = (ctx.model_setting or {}).get("model_id")
        if not model_id:
            raise AppApiException("应用未配置对话模型", code=400)

    def execute(self, ctx: PipelineContext) -> None:
        if ctx.directly_return:
            # 直接返回：用最高命中段落作答，不产生任何流式事件
            ctx.answer = ctx.paragraph_list[0]["content"] if ctx.paragraph_list else "未检索到相关内容。"
            return

        model = self.gateway.get_model(ctx.model_setting["model_id"])
        if ctx.emitter:
            ctx.emitter.emit(SSEEvent(EVT_NODE_START, node_type="ai-chat-node"))

        answer_parts: list[str] = []
        reasoning_parts: list[str] = []
        # 轻量接口：stream() 产出 {"content","reasoning_content"} dict 生成器（非 langchain）
        for chunk in model.stream(ctx.messages):
            content = chunk.get("content") or ""
            reasoning = chunk.get("reasoning_content") or ""
            if content:
                answer_parts.append(content)
                if ctx.emitter:
                    ctx.emitter.emit(SSEEvent(EVT_CONTENT_DELTA, content=content,
                                              reasoning_content="", node_type="ai-chat-node"))
            if reasoning:
                reasoning_parts.append(reasoning)
                if ctx.emitter:
                    ctx.emitter.emit(SSEEvent(EVT_CONTENT_DELTA, content="",
                                              reasoning_content=reasoning, node_type="ai-chat-node"))

        ctx.answer = "".join(answer_parts)
        ctx.reasoning_content = "".join(reasoning_parts)
        ctx.usage = getattr(model, "last_usage", None)      # MaxKBBaseModel 提供的可选属性
        if ctx.emitter:
            ctx.emitter.emit(SSEEvent(EVT_NODE_END, node_type="ai-chat-node", usage=ctx.usage))
            ctx.emitter.emit(SSEEvent(EVT_MESSAGE_END, is_end=True, usage=ctx.usage))