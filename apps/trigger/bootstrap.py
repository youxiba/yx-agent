from .models import Trigger
from .scheduler import register_trigger


def load_all_triggers() -> None:
    """应用启动时把所有启用中的定时触发器重新挂载到调度器（幂等）"""
    for t in Trigger.objects.filter(is_active=True, trigger_type=Trigger.TriggerType.TIMER):
        register_trigger(t)