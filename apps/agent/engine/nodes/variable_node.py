# coding=utf-8
"""变量类节点：variable-assign / splitting / aggregation。"""
from __future__ import annotations
from agent.engine.node import BaseNode, NodeResult, NodeContext


class VariableAssignNode(BaseNode):
    node_type = "variable-assign-node"
    workflow_modes = ("application", "knowledge", "tool")

    def execute(self, ctx: NodeContext) -> NodeResult:
        node_vars, global_vars = {}, {}
        for item in ctx.config.get("variables", []):
            val = ctx.get_field(item["value"]) if isinstance(item.get("value"), str) \
                  and item["value"].startswith("{{") and item["value"].endswith("}}") \
                  else item.get("value")
            target = item.get("target", "global")
            (global_vars if target == "global" else node_vars)[item["variable"]] = val
        return NodeResult(node_vars=node_vars, global_vars=global_vars)


class SplittingNode(BaseNode):
    node_type = "splitting-node"
    workflow_modes = ("application", "knowledge", "tool")

    def execute(self, ctx: NodeContext) -> NodeResult:
        cfg = ctx.config
        source = ctx.get_field(cfg.get("source_ref", ""))
        mode = cfg.get("split_mode", "list")
        if mode == "string":
            out = str(source).split(cfg.get("delimiter", ","))
        else:                                    # list：把列表拆成单个元素列表
            out = [[x] for x in (source or [])]
        return NodeResult(node_vars={"output_list": out})


class AggregationNode(BaseNode):
    node_type = "aggregation-node"
    workflow_modes = ("application", "knowledge", "tool")
    # 该节点 config 需声明 join_mode="AND"，触发 requires_all（AND 合并）

    def execute(self, ctx: NodeContext) -> NodeResult:
        cfg = ctx.config
        refs = cfg.get("source_refs", [])        # 各分支输出引用列表
        collected = [ctx.get_field(r) for r in refs]
        collected = [c for c in collected if c is not None]
        return NodeResult(node_vars={"result_list": collected})