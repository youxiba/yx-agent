# coding=utf-8
from .pg import db

MAX_DIM_HNSW = 2000    # 维度 > 2000 时跳过 HNSW（pgvector 官方限制）


class IndexService:
    """按知识库创建/删除 partial HNSW 索引，命中 WHERE knowledge_id = ..."""

    @staticmethod
    def index_name(knowledge_id: str) -> str:
        return f"idx_{knowledge_id.replace('-', '')}_embedding"

    def create_index(self, knowledge_id: str, dim: int) -> str:
        if dim > MAX_DIM_HNSW:
            return ""
        name = self.index_name(knowledge_id)
        db.execute(
            f"CREATE INDEX IF NOT EXISTS {name} ON embedding "
            f"USING hnsw (vector vector_cosine_ops) "
            f"WHERE knowledge_id = %s AND is_active = true", [knowledge_id])
        return name

    def drop_index(self, knowledge_id: str) -> None:
        db.execute(f"DROP INDEX IF EXISTS {self.index_name(knowledge_id)}")


index_service = IndexService()