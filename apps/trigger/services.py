from common.exceptions import AppApiException
from .models import Trigger


def get_trigger(request, trigger_id: str) -> Trigger:
    """资源隔离：触发器必须属于当前请求的工作空间，否则 403"""
    t = Trigger.objects.filter(id=trigger_id).first()
    if t is None:
        raise AppApiException("触发器不存在", code=404)
    if str(t.workspace_id) != str(request.workspace_id):
        raise AppApiException("无权限访问该触发器", code=403)
    return t