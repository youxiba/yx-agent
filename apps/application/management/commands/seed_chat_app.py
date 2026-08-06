# apps/application/management/commands/seed_chat_app.py
"""创建开发用简单问答应用，打印 access_token 供聊天测试使用。"""
import secrets
from django.core.management.base import BaseCommand
from application.models import Application


class Command(BaseCommand):
    help = "创建简单问答应用，打印 access_token 供聊天测试使用"

    def add_arguments(self, parser):
        parser.add_argument("--name", default="演示问答")
        parser.add_argument("--model-id", default="")
        parser.add_argument("--knowledge-ids", default="")      # 逗号分隔

    def handle(self, *args, **options):
        model_id = options["model_id"]
        knowledge_ids = [i.strip() for i in options["knowledge_ids"].split(",") if i.strip()]
        token = f"sk-chat-{secrets.token_urlsafe(24)}"
        app = Application.objects.create(
            name=options["name"],
            access_token=token,
            model_setting={"model_id": model_id,
                           "system": "你是 MaxKB 助手，请基于检索内容回答。",
                           "temperature": 0.7, "max_tokens": 1024},
            knowledge_setting={"knowledge_ids": knowledge_ids, "search_mode": "blend",
                               "top_n": 3, "similarity": 0.3,
                               "directly_return": True, "direct_return_similarity": 0.9},
        )
        self.stdout.write(f"应用 {app.name} 已创建")
        self.stdout.write(f"app_id      : {app.id}")
        self.stdout.write(f"access_token: {token}")