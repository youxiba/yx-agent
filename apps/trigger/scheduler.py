import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from common.exceptions import AppApiException
from .models import Trigger
from .run import run_trigger

logger = logging.getLogger("trigger.scheduler")

# 内存 JobStore + 显式启动时从 DB 恢复，避免多 worker/多进程重复落库
scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def ensure_started() -> None:
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler 已启动")

def _build_job_trigger(setting: dict):
    """把 DB 里的定时配置翻译成 APScheduler Trigger 对象"""
    mode = setting.get("mode")
    if mode == "cron":
        return CronTrigger.from_crontab(setting["cron"])
    if mode == "interval":
        return IntervalTrigger(seconds=int(setting["interval"]))
    if mode == "daily":
        return CronTrigger(hour=int(setting["hour"]), minute=int(setting["minute"]))
    if mode == "weekly":
        return CronTrigger(day_of_week=str(setting["weekday"]), hour=int(setting["hour"]),
                           minute=int(setting["minute"]))
    if mode == "monthly":
        return CronTrigger(day=int(setting["day"]), hour=int(setting["hour"]), minute=int(setting["minute"]))
    raise AppApiException(f"不支持的触发模式: {mode}", code=400)


def register_trigger(t: Trigger) -> str:
    """注册（或覆盖）一个定时触发器的 APScheduler job；replace_existing 保证幂等"""
    job_id = f"trigger:{t.id}"
    trigger = _build_job_trigger(t.setting)
    ensure_started()
    scheduler.add_job(run_trigger, trigger, id=job_id, args=[str(t.id)], replace_existing=True)
    return job_id


def unregister_trigger(trigger_id) -> None:
    """移除 job；job 不存在时静默（幂等）"""
    job_id = f"trigger:{trigger_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)


