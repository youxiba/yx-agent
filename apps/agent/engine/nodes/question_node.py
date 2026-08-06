# coding=utf-8
"""question-node：用 LLM 把用户问题改写为更适合检索的完整问题。"""
from __future__ import annotations
from agent.engine.node import BaseNode, NodeResult, NodeContext


class QuestionNode(BaseNode):
    node_type = "question-node"
    workflow_modes = ("application",)

    def validate(self, config: dict) -> None:
        assert config.get("model_id"), "question 节点必须指定 model_id"

    def execute(self, ctx: NodeContext) -> NodeResult:
        gateway = ctx.get("gateway")
        model = gateway.get_model(ctx.config["model_id"])
        question = ctx.get_field("chat.question") or ""
        prompt = (
            "你是问题改写助手。把用户问题改写成完整的、可独立检索的句子，只输出改写结果。\n"
            f"用户问题：{question}\n改写："
        )
        rewritten = model.invoke([{"role": "user", "content": prompt}])
        text = getattr(rewritten, "text", None) or (rewritten if isinstance(rewritten, str) else "")
        return NodeResult(node_vars={"question": str(text).strip()},
                          global_vars={"question": str(text).strip()})