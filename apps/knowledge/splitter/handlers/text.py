# coding=utf-8
from ..file import File
from ..spi import BaseSplitHandle, ParagraphRaw, SplitOptions
from ..split_model import SplitModel


class TextSplitHandle(BaseSplitHandle):
    """md/txt 兜底解析器，含多编码检测"""

    def support(self, file: File) -> bool:
        return file.suffix in {".md", ".txt"}

    def get_content(self, file: File, save_image: bool = False) -> str:
        raw = file.open_bytes()
        return raw.decode(self._detect_encoding(raw), errors="ignore")

    @staticmethod
    def _detect_encoding(raw: bytes) -> str:
        for enc in ("utf-8", "gbk", "gb18030", "latin-1"):
            try:
                raw.decode(enc)
                return enc
            except UnicodeDecodeError:
                continue
        return "utf-8"

    def handle(self, file: File, opts: SplitOptions) -> list[ParagraphRaw]:
        text = self.get_content(file, False)
        return SplitModel(opts.content_level_pattern, opts.limit, opts.with_filter).parse_to_paragraphs(text, title=file.file_name)