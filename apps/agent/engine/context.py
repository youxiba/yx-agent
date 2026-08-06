# coding=utf-8
"""ContextStore：global/chat/loop/node 四级命名空间 + 引用解析 + Jinja2 渲染。"""
from __future__ import annotations
import threading
from typing import Any

from jinja2 import Environment, StrictUndefined

_env = Environment(undefined=StrictUndefined)


class ContextStore:
    """上下文服务。注意：所有写操作都持锁（并发 fork 的节点会同时回写 node_vars）。"""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.global_vars: dict[str, Any] = {}
        self.chat_vars: dict[str, Any] = {}
        self.loop_vars: dict[str, Any] = {}
        self.node_vars: dict[str, dict[str, Any]] = {}   # 节点名 -> 该节点输出变量

    # ---------- 回写 ----------
    def write_result(self, node_id: str, node_name: str, node_vars: dict,
                     global_vars: dict | None = None) -> None:
        with self._lock:
            bucket = self.node_vars.setdefault(node_name, {})   # 始终注册节点（记录已执行节点）
            if node_vars:
                bucket.update(node_vars)
            if global_vars:
                self.global_vars.update(global_vars)

    def set_loop(self, **loop_fields: Any) -> None:
        with self._lock:
            self.loop_vars.update(loop_fields)

    # ---------- 引用解析 ----------
    def resolve(self, ref: str) -> Any:
        """解析 '作用域.字段'：scope 为 global/chat/loop 或节点名；字段支持点号下钻。"""
        scope, _, dotted = ref.partition(".")
        if scope == "global":
            return self._lookup(self.global_vars, dotted)
        if scope == "chat":
            return self._lookup(self.chat_vars, dotted)
        if scope == "loop":
            return self._lookup(self.loop_vars, dotted)
        return self._lookup(self.node_vars.get(scope, {}), dotted)

    @staticmethod
    def _lookup(src: Any, dotted: str) -> Any:
        cur = src
        for part in dotted.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
                cur = cur[int(part)]
            else:
                return None
        return cur

    # ---------- 模板渲染 ----------
    def build_jinja_ctx(self, **extra: Any) -> dict[str, Any]:
        """Jinja2 上下文：平铺变量 + chat/global 嵌套作用域 + 节点名作用域 + 额外注入。

        兼容两种模板写法：`{{ chat.question }}`（命名空间）与 `{{ question }}`（平铺）。
        """
        # global 后合并 → 同名键 global 覆盖 chat（节点最新输出优先，如 question 改写）
        ctx: dict[str, Any] = {**self.chat_vars, **self.global_vars}
        ctx["global"] = self.global_vars
        ctx["chat"] = self.chat_vars
        ctx.update(self.node_vars)          # 节点名 -> 该节点输出（'{{ 知识库检索.paragraph_list }}'）
        ctx.update(extra)
        return ctx

    def render(self, template: str, **extra: Any) -> str:
        """渲染模板；未定义变量/缺失字段抛 jinja2.UndefinedError（StrictUndefined）。"""
        return _env.from_string(template).render(self.build_jinja_ctx(**extra))

    # ---------- 持久化快照 ----------
    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {"global": self.global_vars, "chat": self.chat_vars,
                    "loop": self.loop_vars, "node": self.node_vars}

    @classmethod
    def from_dict(cls, data: dict) -> "ContextStore":
        s = cls()
        s.global_vars = dict(data.get("global") or {})
        s.chat_vars = dict(data.get("chat") or {})
        s.loop_vars = dict(data.get("loop") or {})
        s.node_vars = {k: dict(v) for k, v in (data.get("node") or {}).items()}
        return s