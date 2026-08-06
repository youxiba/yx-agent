# coding=utf-8
"""工作流图模型：DAG nodes/edges、前后驱邻接表、循环嵌套标记、JSON <-> 对象互转。"""
from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any


class WorkflowGraphError(Exception):
    """图结构非法（构建/校验失败）。"""


@dataclass
class GraphNode:
    node_id: str
    node_type: str
    name: str = ""
    config: dict = field(default_factory=dict)      # properties
    branch_id: str | None = None                    # 节点固定路由分支（可选）
    loop_container: str | None = None               # 所在最内层循环体 id（循环嵌套标记）


@dataclass
class GraphEdge:
    source: str
    target: str
    branch_id: str | None = None                    # 分支边（condition 输出端）


class WorkflowGraph:
    """DAG：维护 nodes 字典与前后驱邻接表；负责校验与 JSON 互转。"""

    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        self._succ: dict[str, list[GraphEdge]] = defaultdict(list)
        self._pred: dict[str, list[GraphEdge]] = defaultdict(list)

    # ---------- 构建 ----------
    def add_node(self, node: GraphNode) -> None:
        if node.node_id in self.nodes:
            raise WorkflowGraphError(f"重复节点: {node.node_id}")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise WorkflowGraphError(f"边端点不存在: {edge.source} -> {edge.target}")
        self.edges.append(edge)
        self._succ[edge.source].append(edge)
        self._pred[edge.target].append(edge)

    # ---------- 查询 ----------
    def get_node(self, node_id: str) -> GraphNode:
        return self.nodes[node_id]

    def successors(self, node_id: str) -> list[str]:
        """后继节点 id（保留边序，供分支路由使用）。"""
        return [e.target for e in self._succ[node_id]]

    def out_edges(self, node_id: str) -> list[GraphEdge]:
        return self._succ[node_id]

    def predecessors(self, node_id: str) -> list[str]:
        return [e.source for e in self._pred[node_id]]

    def requires_all(self, node_id: str) -> bool:
        """是否 AND 合并（等待全部已激活上游完成）——由节点 config 显式声明。"""
        return self.nodes[node_id].config.get("join_mode") == "AND"

    def get_start(self) -> str:
        """主图入口：唯一无入边且 type==start-node 的节点。"""
        starts = [nid for nid in self.nodes
                  if not self._pred[nid] and self.nodes[nid].node_type == "start-node"]
        if len(starts) != 1:
            raise WorkflowGraphError(f"start 节点必须且只能有 1 个，当前 {len(starts)} 个")
        return starts[0]

    # ---------- 校验 ----------
    def validate(self) -> None:
        """结构校验：边端点存在、唯一 start、无环、循环容器闭合。"""
        for e in self.edges:                                    # 1) 边端点
            if e.source not in self.nodes or e.target not in self.nodes:
                raise WorkflowGraphError(f"边端点不存在: {e.source} -> {e.target}")
        self.get_start()                                        # 2) 唯一 start
        loop_types = {"loop-node", "loop-start-node", "loop-break-node", "loop-continue-node"}
        loop_nodes = {nid for nid, n in self.nodes.items() if n.node_type == "loop-node"}
        for nid, n in self.nodes.items():                       # 3) 循环容器引用合法
            if n.loop_container is not None:
                if n.loop_container not in loop_nodes:
                    raise WorkflowGraphError(f"节点 {nid} 引用不存在的循环容器 {n.loop_container}")
        for lid in loop_nodes:                                  # 4) 每个循环必有 loop-start 入口
            if not any(n.loop_container == lid and n.node_type == "loop-start-node"
                       for n in self.nodes.values()):
                raise WorkflowGraphError(f"循环 {lid} 缺少 loop-start-node 入口")
        self._check_acyclic()                                   # 5) 无环（忽略 loop 回边见 D7 约定）

    def _check_acyclic(self) -> None:
        """Kahn 拓扑排序：主图（不含 loop-container 内部回边）必须无环。"""
        indeg = {nid: 0 for nid in self.nodes}
        for e in self.edges:                                    # 回边 target 指向 loop-node 视为闭环边界
            if e.source != e.target and self.nodes[e.target].loop_container is None:
                indeg[e.target] += 1
        q = deque([nid for nid, d in indeg.items() if d == 0])
        seen = 0
        while q:
            cur = q.popleft()
            seen += 1
            for e in self._succ[cur]:
                if e.target != cur and self.nodes[e.target].loop_container is None:
                    indeg[e.target] -= 1
                    if indeg[e.target] == 0:
                        q.append(e.target)
        if seen != len(self.nodes):
            raise WorkflowGraphError("图中存在环（主图）")

    # ---------- JSON 互转 ----------
    def to_json(self) -> dict[str, Any]:
        return {
            "nodes": [
                {"id": n.node_id, "type": n.node_type, "name": n.name,
                 "properties": n.config, "loop_container": n.loop_container}
                for n in self.nodes.values()
            ],
            "edges": [{"source": e.source, "target": e.target, "branch_id": e.branch_id}
                      for e in self.edges],
        }

    @classmethod
    def from_json(cls, data: dict) -> WorkflowGraph:
        g = cls()
        for nd in data.get("nodes", []):
            g.add_node(GraphNode(
                node_id=nd["id"], node_type=nd["type"],
                name=nd.get("name", nd["id"]), config=nd.get("properties", {}),
                loop_container=nd.get("loop_container")))
        for ed in data.get("edges", []):
            g.add_edge(GraphEdge(source=ed["source"], target=ed["target"],
                                 branch_id=ed.get("branch_id")))
        return g