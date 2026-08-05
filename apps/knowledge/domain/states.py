"""文档/任务显示状态枚举(替代旧版本位图字符串，并做合法流转校验)"""
from django.db.models import TextChoices


class Status(TextChoices):
    """所有文档/段落/任务的统一状态:PENDING->STARTED-> SUCCESS->FAILURE"""
    PENDING = "PENDING" ,"待处理"
    STARTED = "STARTED" ,"处理中"
    SUCCESS = "SUCCESS" ,"成功"
    FAILURE = "FAILURE", "失败"

# 合法状态流转表  （SUCCESS 允许回STARTED用于刷新向量，FAILURE 允许重试）
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    Status.PENDING: {Status.STARTED, Status.FAILURE},
    Status.STARTED: {Status.SUCCESS, Status.FAILURE},
    Status.SUCCESS: {Status.STARTED, Status.FAILURE},
    Status.FAILURE: {Status.PENDING, Status.STARTED},
}

class StateTransitionError(ValueError):
    """非法状态流转"""

def can_transit(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())

def transit(current: str, target: str) -> str:
    """返回合法目标状态：非法则抛出：StateTransitionError"""
    if not can_transit(current, target):
        raise StateTransitionError(f"非法状态流转：{current}->{target}")
    return target