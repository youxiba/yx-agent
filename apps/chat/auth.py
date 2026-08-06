# apps/chat/auth.py
"""聊天认证：应用 access_token / 匿名 client_id / 访问次数限制。"""
import secrets
import uuid
from datetime import date

from application.models import Application
from common.cache import cache_incr
from common.exceptions import AppApiException


class AppChatNumOutOfBounds(AppApiException):
    """访问次数超限（业务码 499，HTTP 200）。"""
    def __init__(self, message="该应用的每日访问次数已达上限"):
        super().__init__(message=message, code=499)


def resolve_application(token: str) -> Application:
    """按应用 Key 解析应用；无效/停用抛 401。"""
    if not token:
        raise AppApiException("缺少应用 Key", code=401)
    app = Application.objects.filter(access_token=token, is_active=True).first()
    if not app:
        raise AppApiException("应用不存在或已停用", code=401)
    return app


def get_chat_application(request, app_id: str) -> Application:
    """从中间件解析出的应用取回并校验与路径 id 一致。"""
    app = getattr(request, "application", None)
    if app is None:
        raise AppApiException("缺少应用 Key", code=401)
    if str(app.id) != str(app_id):
        raise AppApiException("应用不匹配", code=401)
    return app


def ensure_access(app: Application, identity: str) -> None:
    """访问次数限制：按「应用 × 身份 × 日期」计数，超 max_access_count 抛超限。"""
    if app.max_access_count <= 0:
        return
    day = date.today().isoformat()
    key = f"app_access:{app.id}:{identity}:{day}"
    used = cache_incr(key, 1, ttl=86400 * 2)          # 原子自增；TTL 覆盖次日
    if used > app.max_access_count:
        raise AppChatNumOutOfBounds()


def issue_anon_client_id() -> str:
    """未登录端生成匿名身份标识。"""
    return f"anon-{uuid.uuid4().hex[:16]}"