# coding=utf-8
import pytest
from knowledge.splitter.split_model import SplitModel, Node


def test_smart_split_join_identity():
    content = "A。" * 60
    parts = SplitModel(r"^#{1,6} ", 20).smart_split_paragraph(content, 20)
    assert "".join(parts) == content
    assert all(len(p) <= 21 for p in parts)


def test_smart_split_prefers_punctuation():
    content = "短。中间很长很长很长很长没有标点。最后。"
    parts = SplitModel(r"^#{1,6} ", 10).smart_split_paragraph(content, 10)
    # 第一个断点应收在第一个「。」处
    assert parts[0].endswith("。")


def test_parse_to_tree_hierarchy():
    sm = SplitModel(r"^#{1,6} ", 100)
    tree = sm.parse_to_tree("# 一级\nA。\n## 二级\nB。\n# 另一级\nC。")
    assert len(tree.children) == 2
    assert tree.children[0].title == "一级"
    assert tree.children[0].children[0].title == "二级"


def test_parse_to_paragraphs_title_fill():
    sm = SplitModel(r"^#{1,6} ", 50)
    raws = sm.parse_to_paragraphs("# 章节\n正文内容。\n## 小节\n更多内容。", title="根")
    assert raws[0].title == "章节"
    assert raws[1].title == "小节"