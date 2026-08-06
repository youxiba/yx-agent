# coding=utf-8
import re
from .spi import ParagraphRaw


class SplitModel:
    """智能切分：断点优先级 。> ！？> 换行 > 强制截断；Day 4 升级标题树递归"""

    def __init__(self, content_level_pattern: str, limit: int, with_filter: bool = True):
        self.content_level_pattern = content_level_pattern
        self.limit = limit
        self.with_filter = with_filter

    @staticmethod
    def smart_split_paragraph(content: str, limit: int) -> list[str]:
        """在 limit 内从后往前找最优断点，优先级：。> ！？> 换行 > 强制截断"""
        if not content:
            return []
        if len(content) <= limit:
            return [content]
        for ch in "。！？":
            idx = content.rfind(ch, 0, limit)
            if idx >= 0:
                return [content[:idx + 1], *SplitModel.smart_split_paragraph(content[idx + 1:], limit)]
        idx = content.rfind("\n", 0, limit)
        if idx >= 0:
            return [content[:idx + 1], *SplitModel.smart_split_paragraph(content[idx + 1:], limit)]
        return [content[:limit], *SplitModel.smart_split_paragraph(content[limit:], limit)]

    @staticmethod
    def _is_noise(line: str) -> bool:
        line = line.strip()
        return (not line) or line in {"---", "***", "==="}

    def parse_to_paragraphs(self, text: str, title: str = "") -> list[ParagraphRaw]:
        """按空行分组 → 每组智能切分（Day 4 升级为标题树版本）"""
        raws: list[ParagraphRaw] = []
        for block in re.split(r"\n\s*\n", text):
            block = block.strip()
            if not block or (self.with_filter and self._is_noise(block)):
                continue
            for piece in self.smart_split_paragraph(block, self.limit):
                if piece.strip():
                    raws.append(ParagraphRaw(title=title, content=piece.strip()))
        return raws