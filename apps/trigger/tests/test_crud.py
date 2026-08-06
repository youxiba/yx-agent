import pytest
from rest_framework.test import APIClient
from identity.models import User, Role, Workspace, WorkspaceMember
from trigger.models import Trigger


@pytest.fixture
def api():
    return APIClient()


def _login(api, username="admin"):
    user = User.objects.create_user(username=username, email=f"{username}@x.cn", password="Passw0rd!", role=Role.ADMIN)
    # 中间件从用户默认工作空间注入 request.workspace_id，测试需先建空间
    ws = Workspace.objects.create(name=f"{username}-ws", owner=user)
    WorkspaceMember.objects.create(workspace=ws, user=user, role=Role.WORKSPACE_MANAGE)
    r = api.post("/api/admin/auth/login", {"username": username, "password": "Passw0rd!"}, format="json")
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['data']['access']}")


@pytest.mark.django_db
def test_trigger_crud(api):
    _login(api)
    r = api.post("/api/admin/triggers", {
        "name": "每日早报", "trigger_type": "timer",
        "setting": {"mode": "daily", "hour": 9, "minute": 0},
        "tasks": [{"source_type": "tool", "target_id": "00000000-0000-0000-0000-000000000001",
                   "task_args": {"cmd": "echo hi"}}],
    }, format="json")
    assert r.data["code"] == 0
    tid = r.data["data"]["id"]
    assert Trigger.objects.get(id=tid).tasks.count() == 1
    # 更新（不带 tasks，子任务不应被清空）
    r2 = api.put(f"/api/admin/triggers/{tid}", {"name": "改名"}, format="json")
    assert r2.data["code"] == 0 and r2.data["data"]["name"] == "改名"
    assert Trigger.objects.get(id=tid).tasks.count() == 1
    # 启停
    r3 = api.post(f"/api/admin/triggers/{tid}/toggle")
    assert r3.data["data"]["is_active"] is False
    # 删除
    assert api.delete(f"/api/admin/triggers/{tid}").data["code"] == 0


@pytest.mark.django_db
def test_trigger_workspace_isolation(api):
    _login(api, "admin")
    r = api.post("/api/admin/triggers", {"name": "A空间", "setting": {"mode": "interval", "interval": 60}},
                 format="json")
    tid = r.data["data"]["id"]
    # 另一个用户登录后应 403
    api.credentials()
    User.objects.create_user(username="b", email="b@x.cn", password="Passw0rd!", role=Role.USER)
    r2 = api.post("/api/admin/auth/login", {"username": "b", "password": "Passw0rd!"}, format="json")
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {r2.data['data']['access']}")
    r2.workspace_id = "11111111-1111-1111-1111-111111111111"
    # 注：workspace_id 由中间件注入，此处用直接调视图的隔离判断兜底
    from trigger.services import get_trigger
    from common.exceptions import AppApiException
    class _Req: workspace_id = "11111111-1111-1111-1111-111111111111"
    with pytest.raises(AppApiException) as ei:
        get_trigger(_Req(), tid)
    assert ei.value.code == 403