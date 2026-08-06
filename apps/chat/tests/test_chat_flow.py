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

@pytest.mark.django_db
def test_directly_return_skips_llm(api, app_factory, monkeypatch):
    import json
    from types import SimpleNamespace

    def _fake_search(*a, **k):
        return [SimpleNamespace(id="p1", content="命中内容，直接返回", similarity=0.97)]

    monkeypatch.setattr("chat.engine.v1.steps.search_knowledge_step.knowledge_search", _fake_search)
    app = app_factory(knowledge_setting={"knowledge_ids": ["k1"],
                                         "directly_return": True, "direct_return_similarity": 0.9})
    r = api.post(f"/api/chat/{app.id}/chat", {"question": "q"},
                 HTTP_AUTHORIZATION=f"Bearer {app.access_token}", format="json")
    events = [json.loads(ln[6:]) for ln in b"".join(r.streaming_content).decode().split("\n") if ln.startswith("data: ")]
    # 未走 LLM：无 content_delta、无 ai-chat-node
    assert all(e.get("node_type") != "ai-chat-node" for e in events)
    assert "content_delta" not in [e["type"] for e in events]
    from chat.models import ChatRecord
    assert ChatRecord.objects.first().answer == "命中内容，直接返回"


@pytest.mark.django_db
def test_access_limit_via_api(api, app_factory):
    app = app_factory(max_access_count=1)
    for _ in range(2):
        r = api.post(f"/api/chat/{app.id}/chat", {"question": "q", "client_id": "c1"},
                     HTTP_AUTHORIZATION=f"Bearer {app.access_token}", format="json")
    # 第二次调用计数超限 → 业务码 499（HTTP 200 的 JSON 响应）
    assert '"code":499' in r.content.decode()

@pytest.mark.django_db
def test_chat_closed_loop_persist(api, app_factory, monkeypatch):
    from chat.engine.v1.builder import gateway as _g
    from chat.tests.fake_gateway import FakeGateway
    monkeypatch.setattr("chat.engine.v1.builder.gateway", FakeGateway())
    app = app_factory()

    # 1) open 会话
    r = api.post(f"/api/chat/{app.id}/chat/open", {"client_id": "c1"},
                 HTTP_AUTHORIZATION=f"Bearer {app.access_token}", format="json")
    chat_id = r.data["data"]["id"]
    # 2) 发问（携带 chat_id 续聊）
    r2 = api.post(f"/api/chat/{app.id}/chat", {"question": "你好", "chat_id": chat_id},
                  HTTP_AUTHORIZATION=f"Bearer {app.access_token}", format="json")
    assert r2["Content-Type"].startswith("text/event-stream")
    # 消费流：落库发生在 generate() 的 finally，不消费则不落库
    b"".join(r2.streaming_content)
    # 3) 历史可查且记录完整
    r3 = api.get(f"/api/chat/{app.id}/chat/history?chat_id={chat_id}&page=1&page_size=10",
                 HTTP_AUTHORIZATION=f"Bearer {app.access_token}")
    items = r3.data["data"]["items"]
    assert items[-1]["question"] == "你好" and items[-1]["answer"] == "你好"
    # 4) 点赞
    rec_id = items[-1]["id"]
    r4 = api.put(f"/api/chat/{app.id}/chat_record/{rec_id}/vote", {"vote_status": "LIKE"},
                 HTTP_AUTHORIZATION=f"Bearer {app.access_token}", format="json")
    assert r4.data["data"]["vote_status"] == "LIKE"