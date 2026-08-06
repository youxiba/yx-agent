# apps/chat/tests/test_chat_flow.py
"""主对话闭环：SSE 流式响应 + 记录落库。"""
import json

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api():
    return APIClient()


@pytest.mark.django_db
def test_chat_closed_loop(api, app_factory, monkeypatch):
    from chat.engine.v1.builder import gateway as _g
    from chat.tests.fake_gateway import FakeGateway
    monkeypatch.setattr("chat.engine.v1.builder.gateway", FakeGateway())

    app = app_factory()
    r = api.post(f"/api/chat/{app.id}/chat", {"question": "你好"},
                 HTTP_AUTHORIZATION=f"Bearer {app.access_token}", format="json")
    assert r.status_code == 200
    assert r["Content-Type"].startswith("text/event-stream")
    # StreamingHttpResponse 无 content，用 streaming_content 消费
    body = b"".join(r.streaming_content).decode()
    events = [json.loads(ln[6:]) for ln in body.split("\n") if ln.startswith("data: ")]
    assert events[-1]["type"] == "message_end" and events[-1]["is_end"] is True
    from chat.models import ChatRecord
    rec = ChatRecord.objects.get(question="你好")
    assert rec.answer == "你好"
    assert rec.tokens["total_tokens"] == 7