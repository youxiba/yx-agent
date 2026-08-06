from django.apps import AppConfig


class TriggerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trigger"

    def ready(self):
        # runserver 会触发多次 ready（含 autoreload），scheduler 内做幂等启动
        from .scheduler import ensure_started
        ensure_started()
        try:
            from .bootstrap import load_all_triggers
            load_all_triggers()          # 启动时恢复全部启用中的定时触发器
        except Exception:
            # migrate 早期 DB 表未就绪，忽略并在第一次真正注册时报错
            pass