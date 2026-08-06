# coding=utf-8
"""工作流引擎异常。"""
from __future__ import annotations


class WorkflowEngineError(Exception):
    """引擎/图运行期错误（配置非法、深度超限等）。"""


class WorkflowInterrupt(Exception):
    """节点主动中断（form-node 等待用户提交）。携带中断载荷供上层持久化与前端渲染。"""

    def __init__(self, payload: dict | None = None, at_node: str | None = None) -> None:
        self.payload = payload or {}
        self.at_node = at_node
        super().__init__(f"workflow interrupted at {at_node}")