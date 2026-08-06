# coding=utf-8
"""condition-node：按分支条件列表选出命中的 branch_id 输出。"""
from __future__ import annotations
from agent.engine.node import BaseNode, NodeResult, NodeContext
from agent.engine.comparators import evaluate


class ConditionNode(BaseNode):
    node_type = "condition-node"
    workflow_modes = ("application", "knowledge", "tool")

    def validate(self, config: dict) -> None:
        assert isinstance(config.get("branches"), list) and config["branches"], "branches 必填"

    def execute(self, ctx: NodeContext) -> NodeResult:
        resolve = ctx.get_field            # ('变量名.字段' / 'global.xxx' / 常量)
        for br in ctx.config.get("branches", []):
            if evaluate(br.get("conditions", []), resolve):
                return NodeResult(branch_id=br.get("branch_id", "true"))
        return NodeResult(branch_id=ctx.config.get("default_branch_id", "false"))