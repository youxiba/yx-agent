# coding=utf-8
"""执行态持久化：workflow_execution 快照/恢复。"""
from __future__ import annotations

from agent.models import WorkflowExecution
from agent.engine.context import ContextStore
from agent.engine.graph import WorkflowGraph


class ExecutionPersistence:
    def __init__(self, application, chat=None) -> None:
        self.application = application
        self.chat = chat

    def snapshot(self, *, status: str, done_nodes: set[str], next_node: str | None,
                 store: ContextStore, token_usage: dict | None = None,
                 details: dict | None = None) -> str:
        """写入/更新 workflow_execution；返回 exec_id。中断前务必调用以保留断点。"""
        return self._upsert(status, done_nodes, next_node, store, token_usage, details)

    def _upsert(self, status, done_nodes, next_node, store, token_usage, details) -> str:
        obj, _ = WorkflowExecution.objects.get_or_create(
            application=self.application, chat=self.chat,
            defaults={"status": status, "node_graph": self.application.work_flow})
        obj.status = status
        obj.progress = {"done": sorted(done_nodes), "next": next_node}
        obj.context = store.to_dict()
        obj.token_usage = token_usage or {}
        obj.details = details or {}
        obj.is_interrupted = status in (WorkflowExecution.Status.WAIT_USER,
                                        WorkflowExecution.Status.INTERRUPTED)
        obj.save(update_fields=["status", "progress", "context", "token_usage",
                                "details", "is_interrupted", "update_time"])
        return str(obj.id)

    def restore(self, exec_id: str) -> tuple[WorkflowGraph, set[str], ContextStore]:
        """重建图 + done 集合 + 上下文；中断后从第一个未完成节点续跑。"""
        row = WorkflowExecution.objects.get(id=exec_id)
        graph = WorkflowGraph.from_json(row.node_graph)
        done = set(row.progress.get("done", []))
        store = ContextStore.from_dict(row.context or {})
        return graph, done, store