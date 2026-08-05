import json

import pytest
from rest_framework.test import APIClient

from identity.models import User, Role
from model_platform.infra.cipher import cipher
from model_platform.models import Model


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def admin(api):
    User.objects.create_user(username="admin", email="a@x.cn", password="Admin@123", role=Role.ADMIN)
    r = api.post("/api/admin/auth/login", {"username": "admin", "password": "Admin@123"}, format="json")
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['data']['access']}")


@pytest.mark.django_db
def test_cipher_roundtrip():
    blob = cipher.encrypt(json.dumps({"api_key": "sk-abcdef"}))
    assert json.loads(cipher.decrypt(blob))["api_key"] == "sk-abcdef"
    assert cipher.mask("sk-abcdef123456") == "sk-****456"


@pytest.mark.django_db
def test_create_model_mask(api, admin, monkeypatch):
    from model_platform.registry import PROVIDERS
    # openai 无真实 Key 时 is_valid_credential 返回 False → 创建会 400；
    # monkeypatch 跳过凭据校验，专注测"库中密文 + 前端掩码"
    monkeypatch.setattr(PROVIDERS["openai"], "is_valid_credential", lambda *a, **k: True)
    r = api.post("/api/admin/models", {
        "provider": "openai", "model_type": "LLM", "model_name": "gpt-3.5-turbo",
        "name": "m1", "credential": {"api_base": "https://api.openai.com/v1",
                                     "api_key": "sk-1234567890"}}, format="json")
    assert r.data["code"] == 0
    assert "****" in r.data["data"]["credential"]["api_key"]      # 掩码回显
    row = Model.objects.get(name="m1")
    assert "1234567890" not in row.credential                     # 库中是密文


@pytest.mark.django_db
def test_edit_mask_not_overwrite(api, admin):
    row = Model.objects.create(name="m2", provider="openai", model_type="LLM",
                               model_name="gpt-3.5-turbo",
                               credential=cipher.encrypt(json.dumps({"api_key": "sk-REAL123"})),
                               model_params={}, user=None)
    r = api.put(f"/api/admin/models/{row.id}",
                {"credential": {"api_key": "sk-****234"}}, format="json")
    assert r.data["code"] == 0
    assert json.loads(cipher.decrypt(Model.objects.get(id=row.id).credential))["api_key"] == "sk-REAL123"


@pytest.mark.django_db
def test_user_no_model_write(api, admin):
    User.objects.create_user(username="u", email="u@x.cn", password="Admin@123", role=Role.USER)
    r = api.post("/api/admin/auth/login", {"username": "u", "password": "Admin@123"}, format="json")
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['data']['access']}")
    r2 = api.post("/api/admin/models", {}, format="json")
    assert r2.data["code"] == 403
