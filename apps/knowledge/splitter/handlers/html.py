# coding=utf-8
from markdownify import markdownify as md_convert
from ..file import File
from ..spi import BaseSplitHandle, ParagraphRaw, SplitOptions
from ..split_model import SplitModel


class HtmlSplitHandle(BaseSplitHandle):
    def support(self, file: File) -> bool:
        return file.suffix in {".html", ".htm"}

    def get_content(self, file: File, save_image: bool = False) -> str:
        html = file.open_bytes().decode("utf-8", errors="ignore")
        return md_convert(html, heading_style="ATX", strip=["script", "style"])

    def handle(self, file: File, opts: SplitOptions) -> list[ParagraphRaw]:
        text = self.get_content(file, False)
        return SplitModel(opts.content_level_pattern, opts.limit, opts.with_filter).parse_to_paragraphs(text, title=file.file_name)