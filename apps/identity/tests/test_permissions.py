import pytest

from identity.models import Role, User
from identity.permissions import get_user_permissions, P


@pytest.mark.django_db
def test_role_permission_matrix():
    admin = User.objects.create_user(username='a', email='a@x.cn', password='x', role=Role.ADMIN)
    ws_man = User.objects.create_user(username='b', email='b@x.cn', password='x', role=Role.WORKSPACE_MANAGE)
    plain = User.objects.create_user(username='c', email='c@x.cn', password='x', role=Role.USER)

    # ADMIN：全部权限
    assert P.SYSTEM_MANAGE in get_user_permissions(admin)
    assert P.USER_MANAGE in get_user_permissions(admin)
    # WORKSPACE_MANAGE：业务权限，但无 SYSTEM_MANAGE
    assert P.SYSTEM_MANAGE not in get_user_permissions(ws_man)
    assert P.APPLICATION_WRITE in get_user_permissions(ws_man)
    # USER：只读业务权限，无写权限、无系统权限
    assert P.APPLICATION_READ in get_user_permissions(plain)
    assert P.APPLICATION_WRITE not in get_user_permissions(plain)
    assert P.SYSTEM_MANAGE not in get_user_permissions(plain)


@pytest.mark.django_db
def test_require_permission_decorator():
    from common.auth.decorators import require_permissions
    from common.exceptions import PermissionDenied
    from rest_framework.test import APIRequestFactory

    def _mk_user(role):
        return User.objects.create_user(username=role, email=f"{role}@x.cn", password="x", role=role)

    class FakeView:
        @require_permissions(P.USER_MANAGE)
        def get(self, request):
            return "ok"

    factory = APIRequestFactory()

    # 普通 USER 没有 user.manage → 应抛 PermissionDenied
    req = factory.get("/")
    req.user, req.auth = _mk_user(Role.USER), None
    try:
        FakeView().get(req)
        raise AssertionError("USER 调用 user.manage 接口应被拒绝")
    except PermissionDenied:
        pass

    # ADMIN 有全部权限 → 正常返回
    req2 = factory.get("/")
    req2.user, req2.auth = _mk_user(Role.ADMIN), None
    assert FakeView().get(req2) == "ok"
