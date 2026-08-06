# apps/chat/tests/test_openai_compat.py
"""OpenAI 兼容协议：SSE 帧为 choices/delta，结束 data: [DONE]。"""
import json
import pytest


@pytest.mark.django_db
def test_completions_stream(api, app_factory, monkeypatch):
    from chat.engine.v1.builder import gateway as _g
    from chat.tests.fake_gateway import FakeGateway
    monkeypatch.setattr("chat.engine.v1.builder.gateway", FakeGateway())
    app = app_factory()
    r = api.post(f"/api/chat/{app.id}/completions",
                 {"messages": [{"role": "user", "content": "你好"}], "stream": True},
                 HTTP_AUTHORIZATION=f"Bearer {app.access_token}", format="json")
    lines = [ln for ln in b"".join(r.streaming_content).decode().split("\n") if ln.startswith("data: ")]
    assert lines[-1] == "data: [DONE]"
    first = json.loads(lines[0][6:])
    assert first["object"] == "chat.completion.chunk"
    assert first["choices"][0]["delta"]["role"] == "assistant"
    last = json.loads(lines[-2][6:])
    assert last["choices"][0]["finish_reason"] == "stop"
    assert "usage" in last