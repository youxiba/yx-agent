# coding=utf-8
import csv
import io
from ..file import File
from ..spi import BaseSplitHandle, ParagraphRaw, SplitOptions
from ..split_model import SplitModel


class CsvSplitHandle(BaseSplitHandle):
    def support(self, file: File) -> bool:
        return file.suffix == ".csv" and file.meta.get("source_type") != "table"

    def get_content(self, file: File, save_image: bool = False) -> str:
        return self._to_md(self._rows(file))

    def handle(self, file: File, opts: SplitOptions) -> list[ParagraphRaw]:
        sm = SplitModel(opts.content_level_pattern, opts.limit, opts.with_filter)
        return sm.parse_to_paragraphs(self._to_md(self._rows(file)), title=file.file_name)

    @staticmethod
    def _rows(file: File) -> list[list[str]]:
        raw = file.open_bytes().decode("utf-8-sig", errors="ignore")  # 兼容带 BOM 的 Excel 导出
        return [[c.strip() for c in row] for row in csv.reader(io.StringIO(raw))]

    @staticmethod
    def _to_md(rows: list[list[str]]) -> str:
        if not rows:
            return ""
        md = "| " + " | ".join(rows[0]) + " |\n| " + " | ".join("---" for _ in rows[0]) + " |\n"
        for r in rows[1:]:
            md += "| " + " | ".join(r) + " |\n"
        return md