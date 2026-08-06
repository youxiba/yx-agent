from common.redis_lock import redis_lock
from .tasks import execute_trigger_task
from .models import Trigger


def run_trigger(trigger_id: str) -> None:
    """APScheduler/Webhook 共用的触发入口：Redis 锁防重复执行，任务异步入 Celery"""
    with redis_lock(f"trigger:{trigger_id}", timeout=120):
        t = Trigger.objects.filter(id=trigger_id).first()
        if t is None or not t.is_active:
            return
        for task in t.tasks.filter(is_active=True):
            execute_trigger_task.delay(str(task.id))