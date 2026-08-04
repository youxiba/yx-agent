import uuid

from django.conf import settings
from django.db import models


class ModelType(models.TextChoices):
    LLM = "LLM"
    EMBEDDING = "EMBEDDING"
    STT = "STT"
    TTS = "TTS"
    IMAGE = "IMAGE"
    TTI = "TTI"
    RERANKER = "RERANKER"
    TTV = "TTV"
    ITV = "ITV"

class Model(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "SUCCESS"
        ERROR = "ERROR","凭据错误"
        DOWNLOAD = "DOWNLOAD","下载中"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    provider =models.CharField(max_length=64, db_index=True)
    model_type = models.CharField(max_length=32, choices=ModelType.choices)
    model_name = models.CharField(max_length=128)
    credential = models.TextField()
    model_params = models.JSONField(default=dict)
    is_cacheable = models.BooleanField(default=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUCCESS)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    workspace_id = models.CharField(max_length=64, default="default")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "model"
        unique_together = ("provider", "model_type","model_name","workspace_id")