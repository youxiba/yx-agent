import logging
from celery import shared_task

logger = logging.getLogger("trigger.task")


@shared_task
def execute_trigger_task(task_id: str):
    """由各执行器真正执行（Day 3 实现 ApplicationTask/ToolTask）"""
    from .models import TriggerTask
    task = TriggerTask.objects.filter(id=task_id).first()
    if task is None:
        return
    logger.info("执行触发任务 task=%s", task_id)