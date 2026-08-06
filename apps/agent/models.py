import uuid
from django.db import models


class WorkflowExecution(models.Model):
    """执行态持久化：进度/四级命名空间/token/中断标记。支持断点恢复与审计。

    注：Application 模型统一用 application 应用的定义（SIMPLE/WORK_FLOW 同表），
    不在本应用重复定义；本应用只管引擎执行态。
    """
    class Status(models.TextChoices):
        RUNNING = "RUNNING", "运行中"
        SUCCESS = "SUCCESS", "成功"
        FAILURE = "FAILURE", "失败"
        WAIT_USER = "WAIT_USER", "等待用户输入"     # form-node 中断
        INTERRUPTED = "INTERRUPTED", "被打断"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey("application.Application", on_delete=models.CASCADE,
                                    related_name="workflow_executions")
    chat = models.ForeignKey("chat.Chat", null=True, blank=True,
                             on_delete=models.SET_NULL, related_name="workflow_executions")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RUNNING)
    node_graph = models.JSONField(default=dict)      # 发布快照/执行图
    progress = models.JSONField(default=dict)        # {"done": [...], "next": "..."}
    context = models.JSONField(default=dict)         # ContextStore.to_dict()
    token_usage = models.JSONField(default=dict)
    details = models.JSONField(default=dict)
    is_interrupted = models.BooleanField(default=False)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workflow_execution"
