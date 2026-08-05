from django.apps import AppConfig


class ModelPlatformConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "model_platform"

    def ready(self):
        # 装配厂商到 PROVIDERS（只 import，别在此做 DB 查询）
        from .impl.openai import provider  # noqa: F401  触发 register_provider
        from .impl.deepseek import provider as _d  # noqa: F401
        from .impl.qwen import provider as _q  # noqa: F401
        from .impl.ollama import provider as _o
        from .impl.local import provider as _l
