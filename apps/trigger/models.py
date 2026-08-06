# apps/trigger/models.py
import uuid
from django.conf import settings
from django.db import models


class Trigger(models.Model):
    """触发器：定时或 Webhook 触发一批任务（执行应用/工具）"""
    class TriggerType(models.TextChoices):
        TIMER = "timer", "定时触发"
        WEBHOOK = "webhook", "Webhook 触发"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace_id = models.UUIDField(db_index=True)          # 资源隔离
    name = models.CharField(max_length=128)
    trigger_type = models.CharField(max_length=16, choices=TriggerType.choices, default=TriggerType.TIMER)
    # 定时配置：{"mode": "cron|interval|daily|weekly|monthly", ...}
    #   cron    -> {"cron": "0 9 * * *"}
    #   interval-> {"interval": 3600}
    #   daily   -> {"hour": 9, "minute": 0}
    #   weekly  -> {"weekday": "mon", "hour": 9, "minute": 0}
    #   monthly -> {"day": 1, "hour": 9, "minute": 0}
    # Webhook 型额外 {"webhook_secret": "..."} 用于签名校验
    setting = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="triggers")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "trigger"


class TriggerTask(models.Model):
    """触发器下的一个任务：执行一个应用或一个工具"""
    class SourceType(models.TextChoices):
        APPLICATION = "application", "执行应用"
        TOOL = "tool", "执行工具"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trigger = models.ForeignKey(Trigger, on_delete=models.CASCADE, related_name="tasks")
    source_type = models.CharField(max_length=16, choices=SourceType.choices)
    target_id = models.UUIDField()                          # 应用 ID / 工具 ID
    task_args = models.JSONField(default=dict)              # 执行入参
    is_active = models.BooleanField(default=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "trigger_task"


class TaskRecord(models.Model):
    """单次触发任务的执行记录（状态机：PENDING→RUNNING→SUCCESS/FAILURE）"""
    class Status(models.TextChoices):
        PENDING = "PENDING", "等待执行"
        RUNNING = "RUNNING", "执行中"
        SUCCESS = "SUCCESS", "执行成功"
        FAILURE = "FAILURE", "执行失败"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trigger = models.ForeignKey(Trigger, on_delete=models.CASCADE, related_name="records")
    task = models.ForeignKey(TriggerTask, on_delete=models.SET_NULL, null=True, related_name="records")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    execute_result = models.JSONField(null=True, blank=True)    # 成功输出（应用回答 / 工具结果）
    error_message = models.TextField(blank=True, default="")    # 失败原因（截断）
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "task_record"
        indexes = [models.Index(fields=["trigger", "-create_time"])]