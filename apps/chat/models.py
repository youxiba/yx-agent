# apps/chat/models.py
import uuid
from django.conf import settings
from django.db import models


class Chat(models.Model):
    """一次会话（用户与应用之间的一轮持续对话）。"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey("application.Application", on_delete=models.CASCADE, related_name="chats")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    client_id = models.CharField(max_length=64, blank=True, default="", db_index=True)  # 匿名端标识
    chat_type = models.CharField(max_length=16, default="AUDIENCE")   # AUDIENCE=外部访问 / ADMIN=管理端调试
    name = models.CharField(max_length=256, blank=True, default="")   # 会话标题（首问/摘要）
    abstract = models.TextField(blank=True, default="")
    current_chat_record_id = models.CharField(max_length=64, blank=True, default="")  # 最后一条记录 id
    is_deleted = models.BooleanField(default=False)     # 逻辑删除
    delete_time = models.DateTimeField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat"


class ChatRecord(models.Model):
    """一条问答记录。"""
    class VoteStatus(models.TextChoices):
        UN_VOTE = "UN_VOTE", "未投票"
        LIKE = "LIKE", "点赞"
        UNLIKE = "UNLIKE", "点踩"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="records")
    question = models.TextField()
    answer_text_list = models.JSONField(default=list)     # 分片答案（多模态预留）
    answer = models.TextField(blank=True, default="")     # 拼接后的纯文本
    reasoning_content = models.TextField(blank=True, default="")  # 推理模型思考过程
    tokens = models.JSONField(default=dict)               # {"prompt_tokens":..,"completion_tokens":..,"total_tokens":..}
    details = models.JSONField(default=dict)              # 节点执行明细（检索段落等）
    source = models.JSONField(default=list)               # 命中知识来源
    vote_status = models.CharField(max_length=16, choices=VoteStatus.choices, default=VoteStatus.UN_VOTE)
    vote_reason = models.TextField(blank=True, default="")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_record"