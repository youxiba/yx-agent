# coding=utf-8
"""condition-node 比较器：21 个 + AND/OR 断言器。"""
from __future__ import annotations
import re
from typing import Any, Callable

# 比较器签名：Comparator(actual, expect) -> bool
Comparator = Callable[[Any, Any], bool]


def _eq(a, b): return a == b
def _ne(a, b): return a != b


def _num_cmp(a, b, op):
    """数值比较：任一侧非数值 → 返回 False（不抛异常）"""
    na, nb = _num(a), _num(b)
    if na is None or nb is None:
        return False
    return op(na, nb)


def _gt(a, b): return _num_cmp(a, b, lambda x, y: x > y)
def _ge(a, b): return _num_cmp(a, b, lambda x, y: x >= y)
def _lt(a, b): return _num_cmp(a, b, lambda x, y: x < y)
def _le(a, b): return _num_cmp(a, b, lambda x, y: x <= y)
def _contains(a, b): return b in (a or "")
def _not_contains(a, b): return b not in (a or "")
def _is_empty(a, _b): return a in (None, "", [], {})
def _is_not_empty(a, _b): return not _is_empty(a, _b)
def _startswith(a, b): return str(a or "").startswith(str(b))
def _endswith(a, b): return str(a or "").endswith(str(b))
def _len_eq(a, b):
    nb = _num(b)
    return nb is not None and _length(a) == nb


def _len_gt(a, b):
    nb = _num(b)
    return nb is not None and _length(a) > nb


def _len_lt(a, b):
    nb = _num(b)
    return nb is not None and _length(a) < nb


def _len_le(a, b):
    nb = _num(b)
    return nb is not None and _length(a) <= nb
def _regex(a, b): return re.search(str(b), str(a or "")) is not None
def _is_true(a, _b): return bool(a) is True
def _is_false(a, _b): return bool(a) is False
def _in(a, b): return a in (b if isinstance(b, (list, tuple, set, dict)) else str(b or ""))
def _not_in(a, b): return not _in(a, b)


def _num(x) -> float | None:
    """数值化；非数值返回 None（比较器据此返回 False，而非抛异常）"""
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _length(x) -> int:
    if x is None:
        return 0
    return len(x) if hasattr(x, "__len__") else len(str(x))


COMPARATORS: dict[str, Comparator] = {
    "eq": _eq, "ne": _ne, "gt": _gt, "ge": _ge, "lt": _lt, "le": _le,
    "contains": _contains, "not_contains": _not_contains,
    "is_empty": _is_empty, "is_not_empty": _is_not_empty,
    "startswith": _startswith, "endswith": _endswith,
    "length_eq": _len_eq, "length_gt": _len_gt, "length_lt": _len_lt, "length_le": _len_le,
    "regex_match": _regex,
    "is_true": _is_true, "is_false": _is_false,
    "in": _in, "not_in": _not_in,
}


def evaluate(conditions: list[dict], resolve) -> bool:
    """解析一组条件：每条 {field, comparator, value} 用 resolve(field) 取实际值，
    logical_operator in {and, or} 组合。conditions 内每条之间按 logical_operator 连接。"""
    if not conditions:
        return True
    logical = (conditions[0].get("logical_operator") or "and").lower()
    results = [_apply(c, resolve) for c in conditions]
    return all(results) if logical == "and" else any(results)


def _apply(cond: dict, resolve) -> bool:
    field, op = cond["field"], cond["comparator"]
    actual = resolve(field)
    expected = cond.get("value")
    fn = COMPARATORS.get(op)
    if fn is None:
        raise ValueError(f"未知比较器: {op}")
    return fn(actual, expected)