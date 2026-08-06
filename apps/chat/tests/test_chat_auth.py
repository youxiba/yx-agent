# apps/chat/tests/test_chat_auth.py
import pytest
from application.models import Application
from chat.auth import AppChatNumOutOfBounds, ensure_access, resolve_application


@pytest.fixture
def app(db):
    return Application.objects.create(name="t", access_token="sk-test-token",
                                      model_setting={"model_id": "m1"},
                                      knowledge_setting={}, max_access_count=2)


def test_resolve_ok(app):
    assert resolve_application("sk-test-token").id == app.id


def test_resolve_invalid_token(app):
    with pytest.raises(Exception):
        resolve_application("sk-wrong")


def test_access_limit(app):
    ensure_access(app, "c1")
    ensure_access(app, "c1")
    with pytest.raises(AppChatNumOutOfBounds):      # 第 3 次超限
        ensure_access(app, "c1")