# coding=utf-8
import pytest
from knowledge.models import Embedding
from knowledge.infra.vector_store import PGVectorStore, Hit


class FakeEmbeddingModel:
    """测试桩：embed_query 返回固定查询向量，embed_documents 按行返回固定向量"""
    def __init__(self, query_vector):
        self._qv = query_vector

    def embed_query(self, text):
        return self._qv

    def embed_documents(self, texts):
        return [self._qv for _ in texts]


@pytest.mark.django_db
def test_embedding_search_order(knowledge, document, make_paragraph):
    d = 1024
    q = [0.0] * d
    q[0] = 1.0
    pa = make_paragraph(document, content="接近查询的段落")
    pb = make_paragraph(document, content="远离查询的段落")
    va = [0.0] * d
    va[0] = 0.99                                   # 与 q 余弦 ≈ 0.99
    vb = [0.0] * d
    vb[0] = 0.2
    vb[1] = 0.98                                   # 与 q 余弦较低
    Embedding.objects.create(paragraph=pa, document=document, knowledge=knowledge, vector=va, is_active=True)
    Embedding.objects.create(paragraph=pb, document=document, knowledge=knowledge, vector=vb, is_active=True)
    hits = PGVectorStore().query("任意查询", [str(knowledge.id)], "embedding", top_n=2, similarity=0.0,
                                 model=FakeEmbeddingModel(q))
    assert hits[0].paragraph_id == str(pa.id)       # 余弦最近排第一
    assert hits[0].score > hits[1].score


@pytest.mark.django_db
def test_query_group_by_knowledge_merge(knowledge, knowledge2, document, document2, make_paragraph):
    # 两个知识库各有一条高相关段落，跨库查询合并后取 top_n=1 只返回最高分者
    d = 1024
    q = [0.0] * d
    q[0] = 1.0
    pa = make_paragraph(document, content="库1相关")
    pb = make_paragraph(document2, content="库2相关")
    va = [0.0] * d
    va[0] = 0.9
    vb = [0.0] * d
    vb[0] = 0.8
    Embedding.objects.create(paragraph=pa, document=document, knowledge=knowledge, vector=va, is_active=True)
    Embedding.objects.create(paragraph=pb, document=document2, knowledge=knowledge2, vector=vb, is_active=True)
    hits = PGVectorStore().query("x", [str(knowledge.id), str(knowledge2.id)], "embedding",
                                 top_n=1, similarity=0.0, model=FakeEmbeddingModel(q))
    assert len(hits) == 1 and hits[0].paragraph_id == str(pa.id)