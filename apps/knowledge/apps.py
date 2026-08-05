from django.apps import AppConfig


class KnowledgeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "knowledge"

    def ready(self):
        # Day 5 注册领域事件处理器
        from .domain import handlers  # noqa: F401
        handlers.register()