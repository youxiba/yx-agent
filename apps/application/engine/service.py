# apps/application/engine/service.py
# coding=utf-8
"""引擎高层封装：以工具语义运行一次应用工作流（tool-workflow-lib-node 复用）"""
from apps.application.models import Application


def run_application_as_tool(app: Application, inputs: dict, *, chat_id=None, emitter=None) -> dict:
    """把一次应用工作流当作工具调用：
    - 入参注入 start-node 的 global 变量；
    - 运行完整工作流（Phase 5 WorkflowRunner）；
    - 返回 {answer, output}，answer 为最终回复文本，output 为全局变量快照。
    """
    from .workflow_manage import WorkflowRunner
    runner = WorkflowRunner(app, chat_id=chat_id, emitter=emitter)
    runner.context.global_vars.update(inputs)      # 入参作为全局变量注入
    runner.run()                                   # 串行/并发调度（Phase 5 引擎）
    return {"answer": runner.collect_answer(), "output": dict(runner.context.global_vars)}