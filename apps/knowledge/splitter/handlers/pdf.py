# coding=utf-8
from pypdf import PdfReader
from ..file import File
from ..spi import BaseSplitHandle, ParagraphRaw, SplitOptions
from ..split_model import SplitModel


class PdfSplitHandle(BaseSplitHandle):
    def support(self, file: File) -> bool:
        return file.suffix == ".pdf"

    def get_content(self, file: File, save_image: bool = False) -> str:
        parts: list[str] = []
        with open(file.path, "rb") as f:
            reader = PdfReader(f)
            for page in reader.pages:
                parts.append(page.extract_text() or "")
        return "\n".join(parts)

    def handle(self, file: File, opts: SplitOptions) -> list[ParagraphRaw]:
        text = self.get_content(file, False)
        # 大字号行推断为标题（简版：以「字号≥正文*1.5 且行短」为标题行）
        titled = self._infer_headings(text)
        return SplitModel(opts.content_level_pattern, opts.limit, opts.with_filter).parse_to_paragraphs(titled, title=file.file_name)

    @staticmethod
    def _infer_headings(text: str) -> str:
        """把孤立的大写短行转成 markdown 标题（保守启发式，不破坏正文）"""
        lines = []
        for ln in text.splitlines():
            s = ln.strip()
            if s and len(s) <= 40 and s.isupper():
                lines.append(f"## {s}")
            else:
                lines.append(ln)
        return "\n".join(lines)