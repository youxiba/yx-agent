# coding=utf-8
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from .file import File


@dataclass
class SplitOptions:
    """切分选项"""
    limit: int = 256                    # chunk 目标长度（字符）
    with_filter: bool = True            # 过滤空行/分隔线噪音
    content_level_pattern: str = r"^#{1,6} "   # 标题层级正则
    extra: dict = field(default_factory=dict)


@dataclass
class ParagraphRaw:
    """切分产物的中间结构"""
    title: str
    content: str
    keywords: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)   # QA 导入时填充


class BaseSplitHandle(ABC):
    """格式解析责任链节点：support 判断是否接管，handle 产出段落"""
    @abstractmethod
    def support(self, file: File) -> bool: ...

    @abstractmethod
    def handle(self, file: File, opts: SplitOptions) -> list[ParagraphRaw]: ...

    @abstractmethod
    def get_content(self, file: File, save_image: bool) -> str: ...


def get_handler(file: File) -> BaseSplitHandle | None:
    """责任链取第一个命中者（顺序敏感：QA/表格 > 具体格式 > 文本兜底）"""
    from .handlers import SPLIT_HANDLERS
    return next((h for h in SPLIT_HANDLERS if h.support(file)), None)