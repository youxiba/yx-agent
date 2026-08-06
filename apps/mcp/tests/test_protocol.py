# coding=utf-8
"""MCP 暴露端协议一致性测试（raw HTTP 打 JSON-RPC）"""
import json
import pytest
from django.test import Client
from application.models import Application
from identity.models import User, ApiKey
from identity.services import ApiKeyService


@pytest.mark.django_db
def test_mcp_protocol_roundtrip():
    user = User.objects.create_user(username="m", email="m@x.cn", password="x")
    # MCP 认证走应用绑定的 app-key（server.MCPToolHandler 按 ApiKeyService 查）
    app = Application.objects.create(name="demo", user=user, access_token="mcp-token-demo")
    plain_key = ApiKeyService.create(user, "mcp-demo", "application")["key"]
    app.api_key = ApiKey.objects.get(user=user, name="mcp-demo")
    app.save(update_fields=["api_key"])

    c = Client()
    H = {"HTTP_AUTHORIZATION": f"Bearer {plain_key}"}
    rid = 1
    # initialize
    r = c.post("/api/chat/mcp", json.dumps({"jsonrpc": "2.0", "id": rid, "method": "initialize"}), content_type="application/json", **H)
    assert r.json()["result"]["protocolVersion"] == "2025-06-18"
    # tools/list
    r = c.post("/api/chat/mcp", json.dumps({"jsonrpc": "2.0", "id": rid, "method": "tools/list"}), content_type="application/json", **H)
    assert r.json()["result"]["tools"][0]["name"].startswith("agent_")
    # 无 Key → -32000 错误
    r = c.post("/api/chat/mcp", json.dumps({"jsonrpc": "2.0", "id": rid, "method": "tools/list"}), content_type="application/json")
    assert r.json()["error"]["code"] == -32000
    # 未知方法 → -32601
    r = c.post("/api/chat/mcp", json.dumps({"jsonrpc": "2.0", "id": rid, "method": "bogus"}), content_type="application/json", **H)
    assert r.json()["error"]["code"] == -32601