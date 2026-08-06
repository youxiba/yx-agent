# coding=utf-8
"""parameter-extraction-node：LLM 从文本抽取结构化参数（JSON 输出）。"""
from __future__ import annotations
import json
from agent.engine.node import BaseNode, NodeResult, NodeContext
from agent.engine.errors import WorkflowEngineError


class ParameterExtractionNode(BaseNode):
    node_type = "parameter-extraction-node"
    workflow_modes = ("application", "knowledge", "tool")

    def validate(self, config: dict) -> None:
        assert config.get("model_id") and config.get("schema"), "model_id 与 schema 必填"

    def execute(self, ctx: NodeContext) -> NodeResult:
        cfg = ctx.config
        model = ctx.get("gateway").get_model(cfg["model_id"])
        text = ctx.store.render(cfg.get("source", "{{ chat.question }}"))
        prompt = (f"从下面的文本中抽取参数，按 JSON 输出，字段类型如 schema：\n"
                  f"schema: {json.dumps(cfg['schema'], ensure_ascii=False)}\n"
                  f"文本：{text}\nJSON：")
        resp = model.invoke([{"role": "user", "content": prompt}])
        raw = getattr(resp, "text", None) or str(resp)
        try:
            params = json.loads(self._strip_code(raw))
        except json.JSONDecodeError as e:
            raise WorkflowEngineError(f"参数抽取 JSON 解析失败: {e}") from e
        return NodeResult(node_vars={"extracted_params": params})

    @staticmethod
    def _strip_code(raw: str) -> str:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw[raw.find("\n") + 1:] if "\n" in raw else raw
        return raw