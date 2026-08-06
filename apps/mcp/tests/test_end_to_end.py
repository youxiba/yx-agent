# coding=utf-8
"""外部 MCP 客户端 → 本服务 MCP 端点 端到端"""
import asyncio
import pytest
from django.test import Client
from apps.application.models import Application
from apps.identity.models import User
from apps.identity.services import ApiKeyService


@pytest.mark.django_db
def test_external_mcp_client_calls_agent(monkeypatch):
    user = User.objects.create_user(username="m", email="m@x.cn", password="x")
    app = Application.objects.create(name="demo", creator=user)
    created = ApiKeyService.create(user, "mcp-demo", "application")
    app.api_key_id = created["id"]; app.save()

    # 打桩 ChatBridge，避免端到端测试依赖真实 LLM（真实链路在联调清单 12.1 验证）
    import apps.mcp.bridge as bridge_mod
    monkeypatch.setattr(bridge_mod.ChatBridge, "call",
                        lambda self, msg: f"answer for: {msg}")
    c = Client()
    H = {"HTTP_AUTHORIZATION": f"Bearer {created['key']}",
         "content_type": "application/json"}
    # tools/call 走 JSON-RPC
    r = c.post("/api/chat/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                 "params": {"name": f"agent_{app.id.hex[:8]}",
                                            "arguments": {"message": "你好"}}}, **H)
    content = r.json()["result"]["content"]
    assert content[0]["type"] == "text" and content[0]["text"] == "answer for: 你好"