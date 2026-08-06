from .pdf import PdfSplitHandle
from .docx import DocSplitHandle
from .xlsx import XlsxSplitHandle
from .csv_ import CsvSplitHandle
from .html import HtmlSplitHandle
from .zip import ZipSplitHandle
from .qa import QaSplitHandle
from .table import TableSplitHandle
from .text import TextSplitHandle

# 顺序即优先级：QA/表格导入 > 具体格式 > 文本兜底（递归 zip 除外）
SPLIT_HANDLERS: list = [
    QaSplitHandle(), TableSplitHandle(),
    PdfSplitHandle(), DocSplitHandle(), XlsxSplitHandle(), CsvSplitHandle(),
    HtmlSplitHandle(), ZipSplitHandle(), TextSplitHandle(),]