# apps/application/engine/nodes/tool_node.py
# coding=utf-8
"""tool-node：节点内联 Python 代码，经 ToolExecutor 沙箱执行"""
from apps.application.engine.node import BaseNode, NodeContext, NodeResult
from apps.tool.infra.executor import ToolExecutor
from apps.tool.services import validate_inputs
from common.exceptions import AppApiException


class ToolNode(BaseNode):
    node_type = "tool-node"
    workflow_modes = ("application", "knowledge", "tool")

    def execute(self, ctx: NodeContext) -> NodeResult:
        config = ctx.config
        code = config["code"]
        # inputs: {参数名: 字段引用}，运行时把引用解析成实际值
        inputs = {k: ctx.get_field(ref) for k, ref in (config.get("inputs") or {}).items()}
        schema = config.get("input_schema") or {"type": "object"}
        validate_inputs(schema, inputs)
        timeout = int(config.get("timeout", 30))
        result = ToolExecutor().exec_code(code, inputs, timeout=timeout)
        if not result["ok"]:
            raise AppApiException(f"工具执行失败({result['status']}): {result['stderr'][:200]}", code=500)
        return NodeResult(node_vars={"result": result, "output": result.get("output")})