# coding=utf-8
import io
import pytest
from docx import Document as DocxDocument
from openpyxl import Workbook
from knowledge.splitter.file import File
from knowledge.splitter.spi import get_handler, SplitOptions
from knowledge.splitter.handlers.qa import QaSplitHandle
from knowledge.splitter.handlers.table import TableSplitHandle


def _xlsx_bytes() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "人员"
    ws.append(["姓名", "部门"])
    ws.append(["张三", "研发"])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.parametrize("name,bytes_,handler_cls", [
    ("a.docx", None, None),   # 占位，docx 见 test_docx
])
def test_handler_dispatch(name, bytes_, handler_cls):
    ...


def test_xlsx_to_markdown():
    file = File(name="a.xlsx", bytes=_xlsx_bytes())
    raws = get_handler(file).handle(file, SplitOptions())
    joined = "\n".join(r.content for r in raws)
    assert "姓名" in joined and "张三" in joined


def test_qa_md():
    text = "问题1：如何部署？\n回答1：Docker Compose。\n\n问题2：支持 K8s 吗？\n回答2：支持。"
    file = File(name="qa.md", bytes=text.encode(), meta={"source_type": "qa"})
    raws = get_handler(file).handle(file, SplitOptions())
    assert isinstance(get_handler(file), QaSplitHandle)
    assert raws[0].questions == ["问题1：如何部署？"]


def test_table_import():
    file = File(name="t.xlsx", bytes=_xlsx_bytes(), meta={"source_type": "table"})
    raws = get_handler(file).handle(file, SplitOptions())
    assert isinstance(get_handler(file), TableSplitHandle)
    assert raws[0].title == "张三"
    assert "姓名: 张三" in raws[0].content