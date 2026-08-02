from functools import wraps
from identity.permissions import get_user_permissions
from common.exceptions import PermissionDenied


def require_permissions(*perms: str, mode: str = "AND"):
    """perms:权限点，mode = AND/OR 组合判断"""

    def decorator(fn):
        @wraps(fn)
        def wrapper(view, request, *args, **kwargs):
            user = getattr(request, "user", None)
            if user is None or not user.is_authenticated:
                raise PermissionDenied("未登录")
            user_perms = get_user_permissions(user)
            judge = all(p in user_perms for p in perms) if (
                    mode == "AND") else any(p in user_perms for p in perms)
            if not judge:
                raise PermissionDenied("权限不足")
            return fn(view, request, *args, **kwargs)

        return wrapper

    return decorator
