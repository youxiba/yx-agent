# coding=utf-8
"""节点注册表：node_type × workflow_mode 双重索引。"""
from __future__ import annotations
from typing import TYPE_CHECKING

from agent.engine.node import BaseNode

if TYPE_CHECKING:  # 避免顶层循环依赖
    from agent.engine.graph import GraphNode


class NodeRegistry:
    def __init__(self) -> None:
        self._map: dict[tuple[str, str], type[BaseNode]] = {}

    def register(self, node_cls: type[BaseNode]) -> None:
        for mode in node_cls.workflow_modes:
            self._map[(node_cls.node_type, mode)] = node_cls

    def has(self, node_type: str, mode: str) -> bool:
        return (node_type, mode) in self._map

    def create(self, node_type: str, mode: str, config: dict) -> BaseNode:
        cls = self._map.get((node_type, mode))
        if cls is None:
            raise KeyError(f"未注册节点: ({node_type}, {mode})")
        return cls(config)

    def list_types(self, mode: str) -> list[str]:
        """某模式可用节点类型清单（供前端节点目录与 schema 生成）。"""
        return sorted({t for (t, m) in self._map if m == mode})


NODES = NodeRegistry()