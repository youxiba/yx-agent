# coding=utf-8
"""应用工作流执行/恢复编排：chat 视图调用。"""
from __future__ import annotations
from chat.sse import SSEEvent, EventEmitter, EVT_MESSAGE_END
from agent.models import Application, WorkflowExecution
from agent.engine.graph import WorkflowGraph
from agent.engine.context import ContextStore
from agent.engine.node import NodeContext
from agent.engine.executor import Executor
from agent.engine.errors import WorkflowInterrupt
from agent.engine.persistence import ExecutionPersistence


class ApplicationWorkflowService:
    def __init__(self, services: dict) -> None:
        self.services = services

    def execute(self, application: Application, inputs: dict,
                emitter: EventEmitter) -> ContextStore:
        """首次执行；form-node 中断时返回带中断载荷的 store（视图据此响应）。"""
        graph = WorkflowGraph.from_json(application.work_flow)
        store = ContextStore(); store.chat_vars.update(inputs)
        pers = ExecutionPersistence(application)
        ctx = NodeContext(store=store, emitter=emitter, mode="application", node_id="",
                          config={}, services=self._svc(graph, pers))
        executor = Executor(graph)
        services = self.services
        try:
            executor.run(ctx, emitter)
            emitter.emit(SSEEvent(EVT_MESSAGE_END, is_end=True,
                                  answer_text=store.global_vars.get("answer", "")))
        except WorkflowInterrupt as e:
            # 中断点快照（status=WAIT_USER）
            pers.snapshot(status=WorkflowExecution.Status.WAIT_USER,
                          done_nodes=executor.scope.done if executor.scope else set(),
                          next_node=e.at_node, store=store, details={"at_node": e.at_node})
        return store

    def resume(self, execution_id: str, submitted: dict, emitter: EventEmitter) -> ContextStore:
        """用户提交表单后恢复执行：从中断节点续跑。"""
        pers = ExecutionPersistence(Application.objects.get(id=WorkflowExecution.objects
                                                            .get(id=execution_id).application_id))
        graph, done, store = pers.restore(execution_id)
        store.global_vars["_form_submitted"] = submitted
        ctx = NodeContext(store=store, emitter=emitter, mode="application", node_id="",
                          config={}, services=self._svc(graph, pers))
        executor = Executor(graph)
        executor.run(ctx, emitter, start_id=WorkflowExecution.objects.get(id=execution_id)
                     .progress["next"], pre_done=done)
        emitter.emit(SSEEvent(EVT_MESSAGE_END, is_end=True,
                              answer_text=store.global_vars.get("answer", "")))
        return store

    def _svc(self, graph, pers):
        svc = dict(self.services)
        svc.setdefault("graph", graph)
        svc.setdefault("persistence", pers)
        return svc