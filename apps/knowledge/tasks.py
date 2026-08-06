# coding=utf-8
import logging
from celery_once import QueueOnce
from config.celery import celery_app
from .models import Document, DocumentTask, Status, TaskType, VectorType

logger = logging.getLogger("maxkb.knowledge.tasks")


@celery_app.task(base=QueueOnce, once={"keys": ["document_id"], "timeout": 3600}, bind=True)
def split_document(self, document_id: str):
    """切分文档（幂等：同一文档 1h 内只跑一次）"""
    from .services.ingest import DocumentIngestService
    DocumentIngestService().split(document_id)
    return document_id


@celery_app.task(base=QueueOnce, once={"keys": ["document_id"], "timeout": 3600}, bind=True)
def embed_by_document(self, document_id: str):
    """按文档向量化：批量 embed + 落库 + 触发分词"""
    from .services.ingest import DocumentIngestService
    DocumentIngestService().embed_document(document_id)
    return document_id


@celery_app.task(base=QueueOnce, once={"keys": ["knowledge_id"], "timeout": 7200}, bind=True)
def embed_by_knowledge(self, knowledge_id: str):
    """整库重新向量化（改 embedding 模型/批量刷新时调用）"""
    from .services.ingest import DocumentIngestService
    svc = DocumentIngestService()
    for doc_id in Document.objects.filter(knowledge_id=knowledge_id, is_active=True).values_list("id", flat=True):
        svc.embed_document(str(doc_id))
    return knowledge_id


@celery_app.task(base=QueueOnce, once={"keys": ["document_id"], "timeout": 600}, bind=True)
def tokenize_by_document(self, document_id: str):
    """全文分词：重建 embedding.search_vector（tsvector）"""
    from .services.ingest import DocumentIngestService
    DocumentIngestService().tokenize(document_id)
    return document_id