# coding=utf-8
"""start-node：初始化全局变量；把会话输入绑定到 chat 命名空间。"""
from __future__ import annotations
from agent.engine.node import BaseNode, NodeResult, NodeContext


class StartNode(BaseNode):
    node_type = "start-node"
    workflow_modes = ("application", "knowledge", "tool")

    def execute(self, ctx: NodeContext) -> NodeResult:
        global_vars = {}
        for item in ctx.config.get("global_variables", []):
            # item: {"variable": "name", "value": "常量或引用"}
            global_vars[item["variable"]] = self._materialize(item.get("value"), ctx)
        return NodeResult(global_vars=global_vars)

    @staticmethod
    def _materialize(value, ctx):
        if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
            return ctx.store.resolve(value[2:-2].strip())
        return value