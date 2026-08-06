# apps/tool/models.py
# coding=utf-8
"""工具域模型：Tool 工具定义（源码 + input_schema），ToolRecord 执行审计"""
import uuid
from django.conf import settings
from django.db import models


class Tool(models.Model):
    """自定义工具：code 为函数体，input_schema 驱动前端动态表单"""

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "草稿"
        PUBLISHED = "PUBLISHED", "已发布"
        DISABLED = "DISABLED", "已禁用"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=64, unique=True)      # 英文标识，供节点/工具库引用
    label = models.CharField(max_length=128)                 # 展示名
    desc = models.CharField(max_length=512, blank=True, default="")
    code = models.TextField(default="")
    input_schema = models.JSONField(default=dict)            # 驱动前端表单的 JSON Schema
    is_builtin = models.BooleanField(default=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tools")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tool"


class ToolRecord(models.Model):
    """工具执行记录：入参/出参/耗时/状态，只追加不可更新（沙箱审计）"""

    class ResultStatus(models.TextChoices):
        SUCCESS = "SUCCESS", "成功"
        FAILURE = "FAILURE", "失败"
        REJECTED = "REJECTED", "被沙箱拒绝"
        TIMEOUT = "TIMEOUT", "超时"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name="records")
    chat_id = models.UUIDField(null=True, blank=True)         # 关联会话（工具/工作流触发）
    inputs = models.JSONField(default=dict)
    output = models.JSONField(default=dict, null=True, blank=True)
    stdout = models.TextField(blank=True, default="")
    stderr = models.TextField(blank=True, default="")
    status = models.CharField(max_length=16, choices=ResultStatus.choices, default=ResultStatus.SUCCESS)
    run_time_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tool_record"
        indexes = [models.Index(fields=["tool", "-created_at"])]