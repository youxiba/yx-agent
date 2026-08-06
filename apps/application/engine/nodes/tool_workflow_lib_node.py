# apps/application/engine/nodes/tool_workflow_lib_node.py
# coding=utf-8
"""tool-workflow-lib-node：把已发布应用工作流当作工具调用（子工作流）"""
from apps.application.engine.node import BaseNode, NodeContext, NodeResult
from apps.application.models import Application
from apps.application.engine.service import run_application_as_tool
from common.exceptions import AppApiException


class ToolWorkflowLibNode(BaseNode):
    node_type = "tool-workflow-lib-node"
    workflow_modes = ("application",)

    def execute(self, ctx: NodeContext) -> NodeResult:
        config = ctx.config
        app = Application.objects.filter(id=config["application_id"]).first()
        if not app:
            raise AppApiException("子工作流应用不存在", code=404)
        inputs = {k: ctx.get_field(ref) for k, ref in (config.get("inputs") or {}).items()}
        out = run_application_as_tool(app, inputs, chat_id=ctx.chat_id, emitter=ctx.emitter)
        # 记录到主工具对应 ToolRecord（若配置了 audit_tool_name）
        if audit_name := config.get("audit_tool_name"):
            from apps.tool.models import Tool
            from apps.tool.services import record_execution
            tool = Tool.objects.filter(name=audit_name).first()
            if tool:
                record_execution(tool, {"ok": True, "status": "SUCCESS", "output": out,
                                        "stdout": "", "stderr": "", "run_time_ms": 0},
                                 inputs=inputs, chat_id=ctx.chat_id)
        return NodeResult(node_vars={"answer": out["answer"], "output": out["output"]})