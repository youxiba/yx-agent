# coding=utf-8
"""循环节点族：loop-node（容器）+ loop-start（体入口）+ loop-break/continue（控制）。"""
from __future__ import annotations
from agent.engine.node import BaseNode, NodeResult, NodeContext
from agent.engine.context import ContextStore
from agent.engine.errors import WorkflowEngineError


class LoopNode(BaseNode):
    """迭代体子图：mode=ARRAY 遍历列表 / NUMBER 次数 / LOOP 条件式（带 max_loop_count 兜底）。"""
    node_type = "loop-node"
    workflow_modes = ("application", "knowledge", "tool")
    MAX_LOOP = 1000

    def execute(self, ctx: NodeContext) -> NodeResult:
        store: ContextStore = ctx.store
        executor = ctx.get("executor")                    # 当前执行器（run_subgraph）
        mode = ctx.config.get("mode", "ARRAY").upper()
        iterations = self._iterations(ctx, mode)
        body_start = self._find_loop_start(ctx)

        # 嵌套层级计数（写入 global 命名空间，作为 Executor max_depth 的输入）
        depth = int(store.global_vars.get("_loop_depth", 0)) + 1
        store.global_vars["_loop_depth"] = depth
        try:
            for it in iterations:
                store.set_loop(index=it[0], index0=it[0] - 1, item=it[1],
                               list=it[2], **{"_break": False, "_continue": False})
                executor.run_subgraph(body_start, ctx, ctx.emitter, container=ctx.node_id,
                                      depth=depth)
                if store.loop_vars.get("_break"):
                    break
        finally:
            store.global_vars["_loop_depth"] = depth - 1
        return NodeResult(node_vars={"loop_count": len(iterations)})

    def _iterations(self, ctx, mode):
        cfg = ctx.config
        if mode == "ARRAY":
            items = ctx.get_field(cfg.get("loop_list", "")) or []
            if not isinstance(items, list):
                raise WorkflowEngineError("loop_list 引用必须是列表")
            return [(i + 1, v, items) for i, v in enumerate(items)]
        if mode == "NUMBER":
            n = int(ctx.get_field(cfg.get("loop_number", "0")) or 0)
            return [(i + 1, i, list(range(n))) for i in range(n)]
        # LOOP 条件式（while）：条件恒真时靠 MAX_LOOP 兜底
        out, i = [], 0
        while bool(ctx.get_field(cfg.get("loop_condition", ""))) and i < self.MAX_LOOP:
            out.append((i + 1, i, None))
            i += 1
        return out

    def _find_loop_start(self, ctx) -> str:
        for nid, n in ctx.get("graph").nodes.items():
            if n.loop_container == ctx.node_id and n.node_type == "loop-start-node":
                return nid
        raise WorkflowEngineError(f"循环 {ctx.node_id} 缺少 loop-start-node")


class LoopStartNode(BaseNode):
    node_type = "loop-start-node"
    workflow_modes = ("application", "knowledge", "tool")
    def execute(self, ctx): return NodeResult()


class LoopBreakNode(BaseNode):
    node_type = "loop-break-node"
    workflow_modes = ("application", "knowledge", "tool")
    def execute(self, ctx):
        ctx.store.set_loop(_break=True)       # 迭代结束判定在 LoopNode
        return NodeResult()


class LoopContinueNode(BaseNode):
    node_type = "loop-continue-node"
    workflow_modes = ("application", "knowledge", "tool")
    def execute(self, ctx):
        ctx.store.set_loop(_continue=True, _break=True)   # continue 视作本轮提前结束
        return NodeResult()