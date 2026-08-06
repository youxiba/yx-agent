# apps/chat/tests/conftest.py
import pytest
from rest_framework.test import APIClient

from application.models import Application


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def app_factory(db):
    """便捷创建最小 Application（后续各测试复用）。"""
    def _make(**kw):
        return Application.objects.create(
            name=kw.get("name", "t"),
            access_token=kw.get("access_token", "sk-test"),
            model_setting=kw.get("model_setting") or {"model_id": "m1", "system": "test"},
            knowledge_setting=kw.get("knowledge_setting") or {},
            max_access_count=kw.get("max_access_count", 0),
        )
    return _make