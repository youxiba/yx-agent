# coding=utf-8
"""节点 SPI：NodeContext（节点执行视图）+ NodeResult（变量回写）+ BaseNode（接口）。"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from agent.engine.context import ContextStore


class NodeContext:
    """节点执行上下文（ContextStore 的按节点视图）。并发 fork 时每个节点 fork 独立副本，
    共享只读 store/emitter/services，隔离 node_id/config，避免共享可变字典竞态。"""

    def __init__(self, *, store: ContextStore, emitter, mode: str, node_id: str,
                 config: dict, services: dict[str, Any]) -> None:
        self.store = store
        self.emitter = emitter
        self.mode = mode                     # workflow_mode: application/knowledge/tool
        self.node_id = node_id
        self.config = config
        self.services = services             # gateway / vector_store / persistence / executor ...

    def fork(self, node_id: str, config: dict) -> "NodeContext":
        """为单个节点执行创建独立视图（其余引用共享，无深拷贝）。"""
        return NodeContext(store=self.store, emitter=self.emitter, mode=self.mode,
                           node_id=node_id, config=config, services=self.services)

    def get_field(self, ref: str) -> Any:
        """取引用字段：'节点名.字段' / 'loop.index' / 'global.xxx' / 'chat.xxx'。"""
        return self.store.resolve(ref)

    def get(self, key: str) -> Any:
        """取注入服务（gateway / vector_store / executor ...）。"""
        return self.services[key]


@dataclass
class NodeResult:
    """节点执行结果：执行器负责回写各命名空间。"""
    node_vars: dict = field(default_factory=dict)      # 写回 node 命名空间（节点名作用域）
    global_vars: dict = field(default_factory=dict)    # 写回 global 命名空间
    branch_id: str | None = None                       # condition 等节点的分支路由输出


class BaseNode(ABC):
    """节点 SPI：实现 execute 即完成一个节点；validate/recover 有默认空实现。"""
    node_type: str = ""
    workflow_modes: tuple[str, ...] = ("application", "knowledge", "tool")

    def __init__(self, config: dict) -> None:
        self.config = config

    @abstractmethod
    def execute(self, ctx: NodeContext) -> NodeResult:
        """执行节点业务逻辑，返回变量回写结果。"""
        raise NotImplementedError

    def validate(self, config: dict) -> None:
        """参数校验：非法抛 AppApiException/ValueError，执行器统一转 SSE 错误。"""
        pass

    def recover(self, ctx: NodeContext) -> None:
        """从 workflow_execution 断点恢复（默认空实现，重试型节点可覆盖）。"""
        pass