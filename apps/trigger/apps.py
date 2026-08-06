# apps/trigger/apps.py
from django.apps import AppConfig

class TriggerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trigger"
    # Day 2 在 ready() 中启动 APScheduler 并恢复定时器