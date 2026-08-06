# coding=utf-8
import logging
from django.utils import timezone
from common.exceptions import AppApiException
from ..domain.states import transit
from ..domain.events import bus, DocumentIngested, ParagraphEmbedded
from ..file import file_storage
from ..infra.vector_store import PGVectorStore
from ..infra.pg import db
from ..models import Document, DocumentTask, Paragraph, Problem, Status, TaskType, VectorType
from ..splitter.file import File
from ..splitter.spi import SplitOptions, get_handler

logger = logging.getLogger("maxkb.knowledge")


class DocumentIngestService:
    """文档入库编排：上传 → 切分 → 向量化 → 分词（事件链路驱动下游）"""

    def upload(self, knowledge, user, upload, doc_type: str = "base", meta: dict | None = None) -> Document:
        path = file_storage.save(upload)
        doc = Document.objects.create(
            knowledge=knowledge, name=upload.name, type=doc_type,
            meta={"file_path": path, **(meta or {})}, status=Status.PENDING)
        DocumentTask.objects.create(document=doc, type=TaskType.SPLIT, status=Status.PENDING)
        bus.emit(DocumentIngested(document_id=str(doc.id), knowledge_id=str(knowledge.id)))
        return doc

    def split(self, document_id: str) -> Document:
        doc = Document.objects.select_related("knowledge").get(id=document_id)
        task = self._task(doc, TaskType.SPLIT)
        try:
            doc.status = transit(doc.status, Status.STARTED)
            doc.save(update_fields=["status"])
            task.status = Status.STARTED
            task.start_time = timezone.now()
            task.save()
            paragraphs = self._do_split(doc)
            doc.para_count = len(paragraphs)
            doc.char_length = sum(len(p.content) for p in paragraphs)
            doc.status = transit(doc.status, Status.SUCCESS)
            doc.save(update_fields=["para_count", "char_length", "status"])
            task.status = Status.SUCCESS
            task.complete_time = timezone.now()
            task.save()
        except Exception as exc:  # noqa: BLE001
            doc.status = Status.FAILURE
            doc.save(update_fields=["status"])
            task.status = Status.FAILURE
            task.complete_time = timezone.now()
            task.save()
            logger.exception("文档切分失败 document_id=%s", document_id)
            raise exc
        from ..tasks import embed_by_document
        embed_by_document.delay(str(doc.id))      # 切分完成 → 触发向量化
        return doc

    def _do_split(self, doc) -> list[Paragraph]:
        file = File(name=doc.name, path=doc.meta.get("file_path"), meta=doc.meta)
        handler = get_handler(file)
        if handler is None:
            raise AppApiException(f"不支持的文件格式: {file.suffix}", code=400)
        opts = SplitOptions(limit=int(doc.meta.get("limit", 256)))
        raws = handler.handle(file, opts)
        paragraphs = []
        for raw in raws:
            p = Paragraph.objects.create(
                document=doc, knowledge=doc.knowledge,
                title=(raw.title or doc.name)[:256], content=raw.content,
                keywords=raw.keywords, status=Status.PENDING)
            paragraphs.append(p)
            if raw.questions:
                Problem.objects.bulk_create(
                    [Problem(paragraph=p, content=q[:512]) for q in raw.questions], batch_size=100)
        return paragraphs

    def embed_document(self, document_id: str) -> None:
        doc = Document.objects.select_related("knowledge").get(id=document_id)
        if doc.knowledge.vector_type != VectorType.VECTOR:
            self.tokenize(document_id)          # 非向量库只做全文分词
            return
        model_id = doc.knowledge.embedding_model_id or ""
        if not model_id:
            raise AppApiException(f"知识库「{doc.knowledge.name}」未配置 embedding 模型", code=400)
        paragraphs = list(doc.paragraphs.filter(is_active=True).exclude(status=Status.SUCCESS))
        if not paragraphs:
            return
        task = self._task(doc, TaskType.EMBED)
        task.status = Status.STARTED
        task.start_time = timezone.now()
        task.save()
        try:
            from .embedder import EmbeddingService
            vectors = EmbeddingService().embed_documents(model_id, [p.content for p in paragraphs])
            items = [EmbeddingItem(paragraph_id=str(p.id), document_id=str(doc.id),
                                   knowledge_id=str(doc.knowledge_id), text=p.content, vector=v)
                     for p, v in zip(paragraphs, vectors)]
            PGVectorStore().batch_save(items, model_id)
            Paragraph.objects.filter(id__in=[p.id for p in paragraphs]).update(status=Status.SUCCESS)
            task.status = Status.SUCCESS
            task.complete_time = timezone.now()
            task.save()
            doc.status = Status.SUCCESS
            doc.save(update_fields=["status"])
            bus.emit(ParagraphEmbedded(document_id=str(doc.id), paragraph_ids=[str(p.id) for p in paragraphs]))
        except Exception as exc:  # noqa: BLE001
            task.status = Status.FAILURE
            task.complete_time = timezone.now()
            task.save()
            Paragraph.objects.filter(id__in=[p.id for p in paragraphs]).update(status=Status.FAILURE)
            raise exc

    def tokenize(self, document_id: str) -> None:
        db.execute(
            "UPDATE embedding e SET search_vector = "
            "to_tsvector('simple', coalesce(p.content, '') || ' ' || coalesce(p.title, '')) "
            "FROM paragraph p WHERE e.paragraph_id = p.id AND e.document_id = %s", [document_id])
        DocumentTask.objects.filter(document_id=document_id, type=TaskType.TOKENIZE).update(status=Status.SUCCESS)

    @staticmethod
    def _task(doc, task_type) -> DocumentTask:
        task, _ = DocumentTask.objects.update_or_create(
            document=doc, type=task_type, defaults={"status": Status.PENDING, "is_active": True})
        return task

    def refresh_document(self, document_id: str) -> None:
        """文档内容/向量刷新：段落重置为 PENDING，删旧向量后重新向量化"""
        doc = Document.objects.get(id=document_id)
        Paragraph.objects.filter(document=doc, is_active=True).update(status=Status.PENDING)
        PGVectorStore().delete_by_document_ids([str(doc.id)])
        from ..tasks import embed_by_document
        embed_by_document.delay(str(doc.id))