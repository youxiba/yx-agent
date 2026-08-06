# coding=utf-8
import pytest
from knowledge.models import Embedding
from knowledge.infra.vector_store import PGVectorStore, EmbeddingItem
from knowledge.infra.index_service import index_service


@pytest.mark.django_db
def test_batch_save(knowledge, document):
    items = [EmbeddingItem(paragraph_id=str(p.id), document_id=str(document.id),
                           knowledge_id=str(knowledge.id), text=p.content, vector=[0.1] * 1024)
             for p in document.paragraphs.all()]
    PGVectorStore().batch_save(items, "fake-model")    # monkeypatch EmbeddingService 见 conftest
    assert Embedding.objects.filter(knowledge=knowledge).count() == document.paragraphs.count()


@pytest.mark.django_db
def test_hnsw_index_create_drop(knowledge):
    name = index_service.create_index(str(knowledge.id), 1024)
    with pytest.MonkeyPatch().context() as mp:
        from knowledge.infra.pg import db
        rows = db.raw("SELECT indexname FROM pg_indexes WHERE indexname = %s", {"indexname": name} if False else {"indexname": name})
    assert rows
    index_service.drop_index(str(knowledge.id))