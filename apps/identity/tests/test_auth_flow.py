
import pytest
from rest_framework.test import APIClient

from identity.models import Role, User

@pytest.fixture
def api():
    return APIClient()

@pytest.mark.django_db
def test_login_refresh_logout(api):
    User.objects.create_user(username="admin",email="admin@x.cn",password="Admin@123",role=Role.ADMIN)
    r = api.post("/api/admin/auth/login", {"username": "admin", "password": "Admin@123"}, format="json")
    assert r.status_code == 200 and r.data["code"] == 0
    data = r.data["data"]
    assert data["access"] and data["refresh"]

    r2 = api.post("/api/admin/auth/refresh", {"refresh": data["refresh"]}, format="json")
    assert r2.status_code == 200 and r2.data["code"] == 0
    assert r2.data["data"]["access"]


@pytest.mark.django_db
def test_user_manage_permission(api):
    admin = User.objects.create_user(username="admin", email="admin@x.cn", password="Passw0rd!", role=Role.ADMIN)
    plain = User.objects.create_user(username="plain", email="plain@x.cn", password="Passw0rd!", role=Role.USER)
    r = api.post("/api/admin/auth/login", {"username": "admin", "password": "Passw0rd!"}, format="json")
    token = r.data["data"]["access"]
    # admin 可建用户
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    r2 = api.post("/api/admin/users", {"username": "dev02", "email": "d2@x.cn", "password": "Passw0rd!"}, format="json")
    assert r2.data["code"] == 0
    # 普通用户无权限
    api.credentials()
    r3 = api.post("/api/admin/auth/login", {"username": "plain", "password": "Passw0rd!"}, format="json")
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {r3.data['data']['access']}")
    r4 = api.get("/api/admin/users")
    assert r4.data["code"] == 403


@pytest.mark.django_db
def test_api_key_auth(api):
    u = User.objects.create_user(username="svc", email="s@x.cn", password="Passw0rd!")
    from identity.services import ApiKeyService
    created = ApiKeyService.create(u, "聊天机器人", "application")
    r = api.get("/api/admin/users", HTTP_AUTHORIZATION=f"Bearer {created['key']}")   # 无 user.manage → 403
    assert r.data["code"] == 403
