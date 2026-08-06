# coding=utf-8
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from knowledge.models import Embedding


@dataclass
class EmbeddingItem:
    paragraph_id: str
    document_id: str
    knowledge_id: str
    text: str
    vector: list[float] = field(default_factory=list)


@dataclass
class Hit:
    paragraph_id: str
    score: float
    document_id: str = ""
    document_name: str = ""
    title: str = ""
    content: str = ""


class BaseVectorStore(ABC):
    @abstractmethod
    def batch_save(self, items: list[EmbeddingItem], model_id: str) -> None: ...
    @abstractmethod
    def query(self, query_text, knowledge_ids, mode, top_n, similarity, model) -> list[Hit]: ...
    @abstractmethod
    def delete_by_paragraph_ids(self, ids: list[str]) -> None: ...
    @abstractmethod
    def delete_by_document_ids(self, ids: list[str]) -> None: ...
    @abstractmethod
    def delete_by_knowledge_ids(self, ids: list[str]) -> None: ...

class PGVectorStore(BaseVectorStore):
    """pgvector 实现：batch_save 批量写入，query 按知识库分组召回"""

    def batch_save(self, items: list[EmbeddingItem], model_id: str) -> None:
        from ..services.embedder import EmbeddingService
        if not items:
            return
        texts = [it.text for it in items]
        vectors = EmbeddingService().embed_documents(model_id, texts)   # 一次批量网络往返
        rows = [
            Embedding(paragraph_id=it.paragraph_id, document_id=it.document_id,
                      knowledge_id=it.knowledge_id, vector=v, is_active=True)
            for it, v in zip(items, vectors)
        ]
        Embedding.objects.bulk_create(rows, batch_size=100)

    def delete_by_paragraph_ids(self, ids: list[str]) -> None:
        if ids:
            Embedding.objects.filter(paragraph_id__in=ids).delete()

    def delete_by_document_ids(self, ids: list[str]) -> None:
        if ids:
            Embedding.objects.filter(document_id__in=ids).delete()

    def delete_by_knowledge_ids(self, ids: list[str]) -> None:
        if ids:
            Embedding.objects.filter(knowledge_id__in=ids).delete()

    def query(self, query_text, knowledge_ids, mode, top_n, similarity, model) -> list[Hit]:
        # Day 7 完整实现三模式检索（见 Day 7）；Day 6 仅占位保证导入不炸
        return []


# 复用 Day 5 桩的命名，保证 ingest 不重写
EmbeddingItem = EmbeddingItem

# 加载三模式 SQL（收敛进仓储层，替代散落 sql/ 字符串拼接）
_SQL_DIR = Path(__file__).parent / "sql"
EMBEDDING_SEARCH_SQL = (_SQL_DIR / "embedding_search.sql").read_text(encoding="utf-8")
KEYWORDS_SEARCH_SQL = (_SQL_DIR / "keywords_search.sql").read_text(encoding="utf-8")
BLEND_SEARCH_SQL = (_SQL_DIR / "blend_search.sql").read_text(encoding="utf-8")


class PGVectorStore(BaseVectorStore):
    # ...（batch_save / delete_by_* 同 Day 6，省略）

    def query(self, query_text, knowledge_ids, mode, top_n, similarity, model) -> list[Hit]:
        """按知识库分组查询以命中 partial HNSW 索引，结果内存合并降序取 top_n"""
        if not knowledge_ids:
            return []
        vec = model.embed_query(query_text) if mode in ("embedding", "blend") else None
        hits: list[Hit] = []
        for kid in knowledge_ids:
            hits.extend(self._query_single(kid, query_text, vec, mode, top_n * 3, similarity))
        seen: set[str] = set()
        merged: list[Hit] = []
        for h in sorted(hits, key=lambda x: x.score, reverse=True):
            if h.paragraph_id in seen:
                continue
            seen.add(h.paragraph_id)
            merged.append(h)
            if len(merged) >= top_n:
                break
        self._enrich(merged)
        return merged

    def _query_single(self, knowledge_id, query_text, vec, mode, top_n, similarity) -> list[Hit]:
        params = {"k_id": knowledge_id, "top_n": top_n}
        if mode == "keywords":
            params["q"] = query_text
            sql = KEYWORDS_SEARCH_SQL
        elif mode == "blend":
            params.update({"q": vec, "q_text": query_text, "similarity": similarity})
            sql = BLEND_SEARCH_SQL
        else:  # embedding
            params.update({"q": vec, "similarity": similarity})
            sql = EMBEDDING_SEARCH_SQL
        rows = db.raw(sql, params)
        return [Hit(paragraph_id=str(r["paragraph_id"]), score=float(r["score"])) for r in rows]

    @staticmethod
    def _enrich(hits: list[Hit]) -> None:
        if not hits:
            return
        from ..models import Paragraph
        paras = {p.id: p for p in Paragraph.objects.filter(id__in=[h.paragraph_id for h in hits]).select_related("document")}
        for h in hits:
            p = paras.get(h.paragraph_id)
            if p is None:
                continue
            h.title, h.content = p.title, p.content[:500]
            h.document_id = str(p.document_id)
            h.document_name = p.document.name