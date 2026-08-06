# coding=utf-8
"""外部 MCP 客户端 → 本服务 MCP 端点 端到端"""
import json
import pytest
from django.test import Client
from application.models import Application
from identity.models import User
from identity.services import ApiKeyService


@pytest.mark.django_db
def test_external_mcp_client_calls_agent(monkeypatch):
    user = User.objects.create_user(username="m", email="m@x.cn", password="x")
    app = Application.objects.create(name="demo", user=user, access_token="mcp-token-demo")
    created = ApiKeyService.create(user, "mcp-demo", "application")
    app.api_key_id = created["id"]
    app.save(update_fields=["api_key"])

    # 打桩 ChatBridge，避免端到端测试依赖真实 LLM/管线（真实链路在联调清单 12.1 验证）
    import mcp.bridge as bridge_mod
    monkeypatch.setattr(bridge_mod.ChatBridge, "call",
                        lambda self, msg: f"answer for: {msg}")
    c = Client()
    H = {"HTTP_AUTHORIZATION": f"Bearer {created['key']}"}
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": f"agent_{app.id.hex[:8]}",
                       "arguments": {"message": "你好"}}}
    r = c.post("/api/chat/mcp", json.dumps(body), content_type="application/json", **H)
    content = r.json()["result"]["content"]
    assert content[0]["type"] == "text" and content[0]["text"] == "answer for: 你好"
