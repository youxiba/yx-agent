# apps/chat/tests/test_session_api.py
"""会话管理 API：open/历史/详情/改标题/逻辑删除/投票。"""
import pytest
from chat.models import Chat, ChatRecord


@pytest.mark.django_db
def test_session_open_and_delete(api, app_factory):
    app = app_factory()
    r = api.post(f"/api/chat/{app.id}/chat/open", {"client_id": "c1"},
                 HTTP_AUTHORIZATION=f"Bearer {app.access_token}", format="json")
    assert r.data["code"] == 0
    chat_id = r.data["data"]["id"]
    r2 = api.delete(f"/api/chat/{app.id}/chat/{chat_id}/delete",
                    HTTP_AUTHORIZATION=f"Bearer {app.access_token}")
    assert r2.data["code"] == 0
    assert Chat.objects.get(id=chat_id).is_deleted is True


@pytest.mark.django_db
def test_vote(api, app_factory):
    app = app_factory()
    chat = Chat.objects.create(application=app, client_id="c1")
    rec = ChatRecord.objects.create(chat=chat, question="q", answer="a")
    r = api.put(f"/api/chat/{app.id}/chat_record/{rec.id}/vote",
                {"vote_status": "LIKE", "vote_reason": "有用"},
                HTTP_AUTHORIZATION=f"Bearer {app.access_token}", format="json")
    assert r.data["data"]["vote_status"] == "LIKE"


@pytest.mark.django_db
def test_history_paginate(api, app_factory):
    app = app_factory()
    chat = Chat.objects.create(application=app, client_id="c1")
    for i in range(5):
        ChatRecord.objects.create(chat=chat, question=f"q{i}", answer=f"a{i}")
    r = api.get(f"/api/chat/{app.id}/chat/history?chat_id={chat.id}&page=1&page_size=3",
                HTTP_AUTHORIZATION=f"Bearer {app.access_token}")
    assert r.data["data"]["total"] == 5 and len(r.data["data"]["items"]) == 3