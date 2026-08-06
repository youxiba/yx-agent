# apps/chat/serializers.py
from rest_framework import serializers
from .models import Chat, ChatRecord


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ["id", "name", "abstract", "client_id", "current_chat_record_id",
                  "create_time", "update_time"]


class ChatRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRecord
        fields = ["id", "question", "answer", "answer_text_list", "reasoning_content",
                  "tokens", "details", "source", "vote_status", "vote_reason", "create_time"]