# coding=utf-8
import re
from dataclasses import dataclass, field
from .spi import ParagraphRaw


@dataclass
class Node:
    """标题树节点：title/content/children/level"""
    title: str
    content: str = ""
    children: list["Node"] = field(default_factory=list)
    level: int = 0


class SplitModel:
    """智能切分：标题树递归 + smart_split_paragraph 断点 + chunk_size 二次分块"""

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

    def parse_to_tree(self, text: str) -> Node:
        """按标题层级建树：`#{1,6} ` 标题行开新节点，正文累积到当前节点"""
        root = Node(title="", content="")
        stack: list[Node] = [root]
        buf: list[str] = []
        last_level = 0
        for line in text.splitlines():
            m = re.match(self.content_level_pattern, line)
            if m:
                level = m.group(0).count("#")   # 数 # 的数量：`#`→1, `##`→2（修正：原实现剥光 # 全得 0）
                if buf:
                    stack[-1].content += "\n".join(buf).strip() + "\n"
                    buf = []
                node = Node(title=line.lstrip("# ").strip(), level=level)
                while len(stack) > 1 and stack[-1].level >= level:
                    stack.pop()
                stack[-1].children.append(node)
                stack.append(node)
            else:
                buf.append(line)
        if buf:
            stack[-1].content += "\n".join(buf).strip()
        return root

    def parse_to_paragraphs(self, text: str, title: str = "") -> list[ParagraphRaw]:
        """标题树递归 → 每节点内容智能切分，标题取最近层级路径"""
        raws: list[ParagraphRaw] = []

        def walk(node: Node, parent_title: str):
            cur_title = node.title or parent_title
            if node.content.strip():
                for piece in self.smart_split_paragraph(node.content.strip(), self.limit):
                    if piece and not (self.with_filter and self._is_noise(piece)):
                        raws.append(ParagraphRaw(title=cur_title[:256], content=piece))
            for child in node.children:
                walk(child, cur_title)

        walk(self.parse_to_tree(text), title)
        return raws