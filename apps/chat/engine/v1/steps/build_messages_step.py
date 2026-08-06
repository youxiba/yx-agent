# apps/chat/engine/v1/steps/build_messages_step.py
"""拼装消息列表：system 提示 + 检索上下文 + 历史 + 当前问题。"""
from ..context import PipelineContext
from ..pipeline import IBaseStep


class BuildMessagesStep(IBaseStep):
    step_type = "build_messages"

    def execute(self, ctx: PipelineContext) -> None:
        if ctx.directly_return:                     # 直接返回：无需拼消息，留给 ChatStep 兜底
            ctx.messages = []
            return
        ms = ctx.model_setting or {}
        system = ms.get("system") or "你是智能问答助手，请基于提供的资料回答。"
        messages: list[dict] = []

        # 1) system 提示
        messages.append({"role": "system", "content": system})

        # 2) 检索命中段落并入上下文（附编号，引导模型按资料作答）
        if ctx.paragraph_list:
            ctx_text = "\n\n".join(
                f"[{i + 1}] {p.get('content', '')}" for i, p in enumerate(ctx.paragraph_list))
            messages.append({"role": "user",
                             "content": f"以下是检索到的参考资料：\n{ctx_text}\n\n请仅根据这些资料回答问题。"})

        # 3) 多轮历史（最近 N 条，来自 ChatInfoService）
        messages.extend(ctx.chat_history)

        # 4) 当前问题
        messages.append({"role": "user", "content": ctx.optimized_question})

        ctx.messages = messages