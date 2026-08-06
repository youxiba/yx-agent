# coding=utf-8
"""form-node：中断执行等待用户提交表单；恢复后把提交值写入命名空间。"""
from __future__ import annotations
from chat.sse import SSEEvent, EVT_NODE_END
from agent.engine.node import BaseNode, NodeResult, NodeContext
from agent.engine.errors import WorkflowInterrupt


class FormNode(BaseNode):
    node_type = "form-node"
    workflow_modes = ("application",)

    def validate(self, config: dict) -> None:
        assert isinstance(config.get("fields"), list) and config["fields"], "fields 必填"

    def execute(self, ctx: NodeContext) -> NodeResult:
        cfg = ctx.config
        # 已提交则直接消费（恢复路径：execution.context 里带 submitted 值）
        submitted = ctx.store.global_vars.get("_form_submitted", {})
        if submitted:
            return NodeResult(node_vars={"form_data": submitted},
                              global_vars={"form_data": submitted})
        # 未提交：发 node_end(INTERRUPTED) 携带表单定义，然后抛中断
        payload = {"form": cfg["fields"], "execution_id": ctx.services.get("execution_id", "")}
        ctx.emitter.emit(SSEEvent(EVT_NODE_END, node_id=ctx.node_id, node_type="form-node",
                                  node_status="INTERRUPTED", details=payload))
        raise WorkflowInterrupt(payload=payload, at_node=ctx.node_id)