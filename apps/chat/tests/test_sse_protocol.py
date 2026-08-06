# apps/chat/tests/test_sse_protocol.py
import json
from types import SimpleNamespace

import pytest

from chat.sse import EVT_CONTENT_DELTA, EVT_MESSAGE_END, EVT_NODE_START, EventEmitter, SSEEvent


def test_to_frame():
    ev = SSEEvent(type=EVT_CONTENT_DELTA, content="你好", node_type="ai-chat-node")
    frame = ev.to_frame()
    assert frame.startswith("data: ") and frame.endswith("\n\n")
    payload = json.loads(frame[6:].strip())
    assert payload["type"] == "content_delta"
    assert payload["content"] == "你好"


def test_emitter_sequence():
    em = EventEmitter()
    em.emit(SSEEvent(EVT_NODE_START, node_type="search-knowledge-node"))
    em.emit(SSEEvent(EVT_CONTENT_DELTA, content="a"))
    em.emit(SSEEvent(EVT_CONTENT_DELTA, content="b"))
    em.emit(SSEEvent(EVT_MESSAGE_END, usage={"total_tokens": 10}, is_end=True))
    em.close()
    frames = list(em.stream())
    types = [json.loads(f[6:])["type"] for f in frames]
    assert types == ["node_start", "content_delta", "content_delta", "message_end"]
    assert json.loads(frames[-1][6:])["is_end"] is True


@pytest.mark.django_db
def test_chat_event_sequence(api, app_factory, monkeypatch):
    """端到端：reset-problem → search-knowledge → ai-chat 的事件顺序断言。"""
    import json
    from chat.engine.v1.builder import gateway as _g
    from chat.tests.fake_gateway import FakeGateway

    monkeypatch.setattr("chat.engine.v1.builder.gateway", FakeGateway())

    def _fake_search(query_text, knowledge_ids, mode, top_n, similarity):
        return [SimpleNamespace(id="p1", content="MaxKB 支持 Docker/K8s 部署", similarity=0.81)]

    monkeypatch.setattr("chat.engine.v1.steps.search_knowledge_step.knowledge_search", _fake_search)

    app = app_factory(knowledge_setting={"knowledge_ids": ["k1"], "search_mode": "blend",
                                         "top_n": 3, "similarity": 0.3})
    r = api.post(f"/api/chat/{app.id}/chat", {"question": "MaxKB 怎么部署？"},
                 HTTP_AUTHORIZATION=f"Bearer {app.access_token}", format="json")
    events = [json.loads(ln[6:]) for ln in b"".join(r.streaming_content).decode().split("\n") if ln.startswith("data: ")]
    assert [e["type"] for e in events] == [
        "node_start", "node_end",                         # reset-problem
        "node_start", "node_end",                         # search-knowledge
        "node_start",                                     # ai-chat
        "content_delta", "content_delta", "content_delta",
        "node_end",
        "message_end",
    ]
    assert events[0]["node_type"] == "reset-problem-node"
    assert events[2]["node_type"] == "search-knowledge-node"
    assert events[4]["node_type"] == "ai-chat-node"
    assert events[-1]["is_end"] is True