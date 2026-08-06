# coding=utf-8
"""检索引擎统一入口（供 chat 步骤 / API 调用）。

签名与 chat/engine/v1/steps/search_knowledge_step 对齐：
    knowledge_search(query_text, knowledge_ids, mode, top_n, similarity) -> list[Hit]
"""
from ..infra.vector_store import PGVectorStore
from ..models import Knowledge
from .embedder import EmbeddingService


def knowledge_search(query_text: str, knowledge_ids: list[str], mode: str = "embedding",
                     top_n: int = 3, similarity: float = 0.3) -> list:
    """按知识库列表逐一检索，合并按相似度降序取 top_n。返回 Hit 对象列表（含 to_dict）。"""
    model = None
    all_hits: list = []
    store = PGVectorStore()
    for kid in knowledge_ids:
        knowledge = Knowledge.objects.filter(id=kid).first()
        if not knowledge:
            continue
        if model is None:
            if not knowledge.embedding_model_id:
                continue
            model = EmbeddingService().gateway.get_model(knowledge.embedding_model_id)
        hits = store.query(query_text, [str(knowledge.id)], mode, top_n, similarity, model)
        all_hits.extend(hits)
    all_hits.sort(key=lambda h: h.score, reverse=True)
    return all_hits[:top_n]
