# apps/application/models.py
import uuid
from django.conf import settings
from django.db import models


class Application(models.Model):
    """应用：type=SIMPLE（线性流水线）/ WORK_FLOW（DAG 工作流）同表。

    Phase 4 定义 SIMPLE；Phase 5 补充 WORK_FLOW 类型 + work_flow 图字段。
    """
    class Type(models.TextChoices):
        SIMPLE = "SIMPLE", "简单问答"      # 线性流水线（引擎 V1）
        WORK_FLOW = "WORK_FLOW", "工作流"  # DAG 工作流（引擎 V2）

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    desc = models.TextField(blank=True, default="")
    app_type = models.CharField(max_length=16, choices=Type.choices, default=Type.SIMPLE)
    work_flow = models.JSONField(default=dict)   # WORK_FLOW 应用的 DAG 图 JSON
    access_token = models.CharField(max_length=128, unique=True, db_index=True)  # 应用 Key（聊天认证用）
    # 模型设置：{"model_id": "...", "system": "提示词", "temperature": 0.7, "max_tokens": 1024}
    model_setting = models.JSONField(default=dict)
    # 知识库设置：{"knowledge_ids": [...], "search_mode": "embedding", "top_n": 3, "similarity": 0.3,
    #             "directly_return": true, "direct_return_similarity": 0.9}
    knowledge_setting = models.JSONField(default=dict)
    max_access_count = models.IntegerField(default=0)   # 0 表示不限访问次数（按日计数）
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    workspace_id = models.CharField(max_length=64, default="default")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "application"


class ApplicationVersion(models.Model):
    """发布快照：发布时拷贝 work_flow，运行时读已发布版本。"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="versions")
    work_flow_snapshot = models.JSONField(default=dict)
    is_published = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "application_version"