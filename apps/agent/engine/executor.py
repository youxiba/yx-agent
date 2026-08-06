# coding=utf-8
"""Executor V2：并发 DAG 调度器。
- 执行模型：每个节点一个线程池任务；后继节点在『前驱完成后才提交』，天然数据依赖串行，
  多后继并发 fork。无递归，规避 RecursionError。
- 并发安全：done/activated 属于 _Scope 并由 scope.lock 保护；ContextStore.write_result 自锁。
- AND 合并：requires_all 节点只等『已激活』上游完成（被分支跳过的上游不阻塞）。
- 中断：节点抛 WorkflowInterrupt 时 abort scope，停止调度新节点。
"""
from __future__ import annotations
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from chat.sse import SSEEvent, EventEmitter, EVT_NODE_START, EVT_NODE_END
from agent.engine.errors import WorkflowEngineError, WorkflowInterrupt
from agent.engine.graph import WorkflowGraph, GraphNode
from agent.engine.registry import NODES
from agent.engine.node import NodeContext, NodeResult


class _Scope:
    """一次执行范围（主图或一次循环体迭代）的完成计数 + done/activated + 首个异常。"""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.pending = 0
        self.done: set[str] = set()
        self.activated: set[str] = set()
        self.error: BaseException | None = None
        self._idle = threading.Event()

    def acquire(self) -> None:
        with self.lock:
            self.pending += 1

    def release(self) -> None:
        with self.lock:
            self.pending -= 1
            if self.pending == 0 and self.error is None:
                self._idle.set()

    def abort(self, exc: BaseException) -> None:
        with self.lock:
            if self.error is None:
                self.error = exc
            self.pending = 0
            self._idle.set()

    def wait(self) -> None:
        self._idle.wait()


class Executor:
    def __init__(self, graph: WorkflowGraph, pool_size: int = 16, max_depth: int = 64) -> None:
        self.graph = graph
        self.pool_size = pool_size
        self.max_depth = max_depth
        self.pool: ThreadPoolExecutor | None = None

    # ---------- 顶层入口 ----------
    def run(self, ctx: NodeContext, emitter: EventEmitter, start_id: str | None = None,
            pre_done: set[str] | None = None) -> None:
        """运行整图。pre_done 供断点恢复时预置已完成节点（D8）。"""
        start_id = start_id or self.graph.get_start()
        self.pool = ThreadPoolExecutor(max_workers=self.pool_size)
        scope = _Scope()
        self.scope = scope                       # 暴露供中断后 snapshot 取 done 集合
        scope.done = set(pre_done or ())
        try:
            scope.acquire()
            self._submit(start_id, ctx, emitter, depth=0, container=None, scope=scope)
            scope.wait()
        finally:
            self.pool.shutdown(wait=True)
        if scope.error is not None:
            raise scope.error

    # ---------- 循环体子图（D7 使用） ----------
    def run_subgraph(self, entry_id: str, ctx: NodeContext, emitter: EventEmitter,
                     container: str, depth: int) -> _Scope:
        """运行循环体子图：只调度 loop_container == container 的节点；独立 scope 计数。"""
        scope = _Scope()
        scope.acquire()
        self._submit(entry_id, ctx, emitter, depth=depth + 1, container=container, scope=scope)
        scope.wait()
        if scope.error is not None:
            raise scope.error
        return scope

    # ---------- 调度核心 ----------
    def _submit(self, node_id: str, ctx: NodeContext, emitter: EventEmitter, *,
                depth: int, container: str | None, scope: _Scope) -> None:
        assert self.pool is not None
        self.pool.submit(self._run_node, node_id, ctx, emitter, depth, container, scope)

    def _run_node(self, node_id: str, ctx: NodeContext, emitter: EventEmitter,
                  depth: int, container: str | None, scope: _Scope) -> None:
        if depth > self.max_depth:
            scope.abort(WorkflowEngineError(f"执行深度超限（> {self.max_depth}），疑似循环未收敛"))
            return
        try:
            result = self._execute_one(node_id, ctx, emitter)
            with scope.lock:
                scope.done.add(node_id)
            nxt = self._next_nodes(node_id, ctx, container, scope, result.branch_id)
        except WorkflowInterrupt as e:
            e.at_node = node_id
            scope.abort(e)                     # 中断：停止调度新节点
            return
        except BaseException as e:             # 其余异常聚合，等全部结束统一抛出
            scope.abort(e)
            return
        for n in nxt:
            scope.acquire()
        scope.release()
        for n in nxt:
            self._submit(n, ctx, emitter, depth=depth + 1, container=container, scope=scope)

    def _execute_one(self, node_id: str, ctx: NodeContext, emitter: EventEmitter) -> NodeResult:
        node = self.graph.get_node(node_id)
        inst = NODES.create(node.node_type, ctx.mode, node.config)
        inst.validate(node.config)
        emitter.emit(SSEEvent(EVT_NODE_START, node_id=node_id, node_type=node.node_type))
        result: NodeResult = inst.execute(ctx.fork(node_id, node.config))
        ctx.store.write_result(node_id, node.name, result.node_vars, result.global_vars)
        emitter.emit(SSEEvent(EVT_NODE_END, node_id=node_id, node_status="SUCCESS"))
        return result

    # ---------- 后继选择（分支/容器边界/AND 合并） ----------
    def _next_nodes(self, node_id: str, ctx: NodeContext, container: str | None,
                    scope: _Scope, branch_id: str | None) -> list[str]:
        out: list[str] = []
        with scope.lock:                       # 读 done/activated 必须持锁
            for edge in self.graph.out_edges(node_id):
                n = edge.target
                node = self.graph.get_node(n)
                if container is not None and node.loop_container != container:
                    continue                   # 子图边界：跳过容器外节点
                if container is None and node.loop_container is not None:
                    continue                   # 主图边界：循环体节点由 loop 节点自行调度
                if edge.branch_id is not None and edge.branch_id != branch_id:
                    continue                   # 分支边路由（D6 生效）
                if n in scope.done:
                    continue
                if n in scope.activated:
                    continue
                if not self.graph.requires_all(n):
                    out.append(n)
                else:                          # AND 合并：只等已激活上游
                    active_preds = [p for p in self.graph.predecessors(n) if p in scope.activated]
                    if all(p in scope.done for p in active_preds):
                        out.append(n)
            for n in out:
                scope.activated.add(n)
        return out