# coding=utf-8
import uuid
from django.db import models
from pgvector.django import VectorField
from .domain.states import Status


class KnowledgeType(models.TextChoices):
    BASE = "base", "基础知识库"
    WEB = "web", "Web 知识库"

class VectorType(models.TextChoices):
    VECTOR = "vector", "向量检索"
    SUPPORTED = "supported", "仅全文检索（不支持向量）"

class DocumentType(models.TextChoices):
    BASE = "base", "基础文档"
    QA = "qa", "QA 文档"
    WEB = "web","WEB文档"

class TaskType(models.TextChoices):
    SPLIT = "split", "切分"
    EMBED = "embed","向量化"
    TOKENIZE = "tokenize", "全文分词"

class Knowledge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    embedding_model_id = models.CharField(max_length=64, blank=True, default="")  # model_platform.Model.id
    vector_type = models.CharField(max_length=32, choices=VectorType.choices, default=VectorType.VECTOR)
    index_name = models.CharField(max_length=128, default="maxkb_embedding")  # HNSW 索引名
    type = models.CharField(max_length=32, choices=KnowledgeType.choices, default=KnowledgeType.BASE)
    workspace = models.ForeignKey("identity.Workspace", on_delete=models.CASCADE, related_name="knowledges")
    user = models.ForeignKey("identity.User", on_delete=models.CASCADE, related_name="knowledges")
    folder = models.ForeignKey("KnowledgeFolder", on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="knowledges")
    meta = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "knowledge"
        ordering = ["-update_time"]


class KnowledgeFolder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    knowledge = models.ForeignKey(Knowledge, on_delete=models.CASCADE, related_name="folders")
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    name = models.CharField(max_length=128)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_folder"


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    knowledge = models.ForeignKey(Knowledge, on_delete=models.CASCADE, related_name="documents")
    folder = models.ForeignKey(KnowledgeFolder, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="documents")
    name = models.CharField(max_length=256)
    type = models.CharField(max_length=32, choices=DocumentType.choices, default=DocumentType.BASE)
    char_length = models.IntegerField(default=0)
    para_count = models.IntegerField(default=0)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    is_active = models.BooleanField(default=True)
    meta = models.JSONField(default=dict, blank=True)  # 记录 file_path/web_url/limit/标签等
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "document"
        ordering = ["-update_time"]


class DocumentTask(models.Model):
    """独立 document_task 子表：记录多任务（切分/向量化/分词）各自进度，替代旧版位图字符串"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="tasks")
    type = models.CharField(max_length=32, choices=TaskType.choices)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    queue = models.CharField(max_length=32, default="celery")  # celery/model
    meta = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    submit_time = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True, blank=True)
    complete_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "document_task"
        constraints = [models.UniqueConstraint(fields=["document", "type"], name="uniq_doc_task_type")]


class Paragraph(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="paragraphs")
    knowledge = models.ForeignKey(Knowledge, on_delete=models.CASCADE, related_name="paragraphs")
    title = models.CharField(max_length=256, default="")
    content = models.TextField(blank=True, default="")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    is_active = models.BooleanField(default=True)
    keywords = models.JSONField(default=list, blank=True)
    version = models.IntegerField(default=1)  # 内容变更版本号
    compare_content_hash = models.CharField(max_length=64, default="")  # 内容去重哈希
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "paragraph"
        ordering = ["create_time"]


class Problem(models.Model):
    """关联段落的问题（用于命中测试时的问题匹配）"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paragraph = models.ForeignKey(Paragraph, on_delete=models.CASCADE, related_name="problems")
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "problem"


class Termbase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    workspace = models.ForeignKey("identity.Workspace", on_delete=models.CASCADE, related_name="termbases")
    user = models.ForeignKey("identity.User", on_delete=models.CASCADE, related_name="termbases")
    is_active = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "termbase"


class Term(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    termbase = models.ForeignKey(Termbase, on_delete=models.CASCADE, related_name="terms")
    content = models.CharField(max_length=256)
    is_active = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "term"


class Embedding(models.Model):
    """段落向量存储：vector 为 pgvector 字段，search_vector 为 tsvector（Day 7 迁移补充）"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paragraph = models.ForeignKey(Paragraph, on_delete=models.CASCADE, related_name="embeddings")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="embeddings")
    knowledge = models.ForeignKey(Knowledge, on_delete=models.CASCADE, related_name="embeddings")
    index_name = models.CharField(max_length=128, default="maxkb_embedding")
    vector = VectorField(null=True, blank=True)  # 维度由 embedding 模型决定（迁移时按实际调）
    meta = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "embedding"