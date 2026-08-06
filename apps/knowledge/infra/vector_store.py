# coding=utf-8
from dataclasses import dataclass, field


@dataclass
class EmbeddingItem:
    paragraph_id: str
    document_id: str
    knowledge_id: str
    text: str
    vector: list[float] = field(default_factory=list)


class PGVectorStore:
    """Day 5 最小桩：仅落 Paragraph 状态；Day 6 重写为真实向量写入"""
    def batch_save(self, items: list[EmbeddingItem], model_id: str) -> None:
        return None