# coding=utf-8
from common.exceptions import AppApiException
from ..infra.vector_store import PGVectorStore


class RetrievalService:
    """命中测试 + 检索统一入口"""

    def hit_test(self, knowledge, query: str, mode: str = "embedding",
                 top_n: int = 3, similarity: float = 0.5) -> list[dict]:
        from .embedder import EmbeddingService
        model_id = knowledge.embedding_model_id
        if not model_id:
            raise AppApiException(f"知识库「{knowledge.name}」未配置 embedding 模型", code=400)
        model = EmbeddingService().gateway.get_model(model_id)   # 复用单例 gateway
        hits = PGVectorStore().query(query, [str(knowledge.id)], mode, top_n, similarity, model)
        return [{"paragraph_id": h.paragraph_id, "score": round(h.score, 4),
                 "document_id": h.document_id, "document_name": h.document_name,
                 "title": h.title, "content": h.content} for h in hits]