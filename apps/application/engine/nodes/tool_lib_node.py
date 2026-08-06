# apps/application/engine/nodes/tool_lib_node.py
# coding=utf-8
"""tool-lib-node：引用工具库中已发布(PUBLISHED)的工具，执行并落 ToolRecord 审计"""
from apps.application.engine.node import BaseNode, NodeContext, NodeResult
from apps.tool.models import Tool
from apps.tool.infra.executor import ToolExecutor
from apps.tool.services import validate_inputs, record_execution
from common.exceptions import AppApiException


class ToolLibNode(BaseNode):
    node_type = "tool-lib-node"
    workflow_modes = ("application", "knowledge", "tool")

    def execute(self, ctx: NodeContext) -> NodeResult:
        config = ctx.config
        tool = Tool.objects.filter(name=config["tool_name"], status=Tool.Status.PUBLISHED).first()
        if not tool:
            raise AppApiException(f"工具库中不存在已发布工具: {config['tool_name']}", code=404)
        inputs = {k: ctx.get_field(ref) for k, ref in (config.get("inputs") or {}).items()}
        validate_inputs(tool.input_schema, inputs)
        timeout = int(config.get("timeout", 30))
        result = ToolExecutor().exec_code(tool.code, inputs, timeout=timeout)
        record_execution(tool, result, inputs=inputs, chat_id=ctx.chat_id)   # 审计
        if not result["ok"]:
            raise AppApiException(f"工具 {tool.label} 执行失败({result['status']}): {result['stderr'][:200]}", code=500)
        return NodeResult(node_vars={"result": result, "output": result.get("output")})