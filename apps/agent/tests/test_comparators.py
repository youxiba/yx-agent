import pytest
from agent.engine.comparators import COMPARATORS, evaluate


def test_all_21_registered():
    assert len(COMPARATORS) == 21
    for op in ["eq", "ne", "gt", "ge", "lt", "le", "contains", "not_contains",
               "is_empty", "is_not_empty", "startswith", "endswith",
               "length_eq", "length_gt", "length_lt", "length_le", "regex_match",
               "is_true", "is_false", "in", "not_in"]:
        assert op in COMPARATORS


def test_numeric_and_string():
    assert COMPARATORS["gt"](2, 1) and not COMPARATORS["gt"]("a", 1)
    assert COMPARATORS["contains"]("hello", "ell")
    assert COMPARATORS["startswith"]("MaxKB", "Max")
    assert COMPARATORS["length_gt"]("abcd", 3)
    assert COMPARATORS["regex_match"]("abc123", r"\d+")


def test_evaluate_and_or():
    resolve = lambda f: {"x": 1, "y": 2}.get(f)
    conds = [{"field": "x", "comparator": "eq", "value": 1, "logical_operator": "and"},
             {"field": "y", "comparator": "gt", "value": 1}]
    assert evaluate(conds, resolve) is True
    conds[1]["comparator"] = "lt"
    assert evaluate(conds, resolve) is False
    conds2 = [{"field": "x", "comparator": "eq", "value": 1, "logical_operator": "or"},
              {"field": "y", "comparator": "lt", "value": 1}]
    assert evaluate(conds2, resolve) is True