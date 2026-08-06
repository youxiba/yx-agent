import pytest
from agent.engine.context import ContextStore


def test_namespaces_and_resolve():
    s = ContextStore()
    s.write_result("n1", "知识库检索", {"paragraph_list": [{"title": "a"}, {"title": "b"}]})
    s.write_result("n2", "回复", {"answer": "你好"})
    s.global_vars["company"] = "MaxKB"
    s.chat_vars["question"] = "是什么"
    s.set_loop(index=1, item="x", list=[1, 2])

    assert s.resolve("知识库检索.paragraph_list") == [{"title": "a"}, {"title": "b"}]
    assert s.resolve("知识库检索.paragraph_list.0.title") == "a"
    assert s.resolve("global.company") == "MaxKB"
    assert s.resolve("chat.question") == "是什么"
    assert s.resolve("loop.index") == 1
    assert s.resolve("不存在的节点.字段") is None


def test_render_strict_undefined():
    s = ContextStore()
    s.write_result("n1", "检索", {"paragraph_list": [{"title": "a"}]})
    s.global_vars["company"] = "MaxKB"
    out = s.render("公司{{ company }} 首段：{{ 检索.paragraph_list.0.title }}")
    assert out == "公司MaxKB 首段：a"
    with pytest.raises(Exception):        # StrictUndefined -> jinja2.UndefinedError
        s.render("{{ 不存在的变量 }}")


def test_dict_roundtrip():
    s = ContextStore()
    s.write_result("n1", "回复", {"answer": "hi"})
    s.global_vars["x"] = 1
    s2 = ContextStore.from_dict(s.to_dict())
    assert s2.resolve("回复.answer") == "hi"
    assert s2.resolve("global.x") == 1