# apps/mcp/server.py
# coding=utf-8
"""MCP 暴露端：把 MaxKB 应用暴露为一个 MCP 工具（agent_xxx）。

JSON-RPC 2.0：initialize / tools/list / tools/call；协议版本 2025-06-18。
"""
import json
from application.models import Application
from identity.services import ApiKeyService
from common.exceptions import AppApiException


class MCPToolHandler:
    PROTOCOL = "2025-06-18"

    def __init__(self, api_key_token: str):
        self.app = self._authenticate(api_key_token)

    def _authenticate(self, token: str) -> Application:
        """Bearer → ApiKeyService.authenticate → 绑定该 Key 的 Application"""
        ak = ApiKeyService.authenticate(token)
        if not ak:
            raise AppApiException("MCP: 无效的应用 Key", code=401)
        app = Application.objects.filter(api_key=ak).first()
        if not app:
            raise AppApiException("MCP: 应用 Key 未绑定应用", code=403)
        return app

    def initialize(self) -> dict:
        return {"protocolVersion": self.PROTOCOL, "capabilities": {"tools": {}},
                "serverInfo": {"name": "maxkb-mcp", "version": "1.0.0"}}

    def list_tools(self) -> dict:
        return {"tools": [{
            "name": f"agent_{self.app.id.hex[:8]}",
            "description": self.app.desc or f"MaxKB 应用 {self.app.name}",
            "inputSchema": {"type": "object",
                            "properties": {"message": {"type": "string"}},
                            "required": ["message"]},
        }]}

    def call_tool(self, params: dict) -> dict:
        text = self._run_chat(params["arguments"]["message"])    # 内部建会话 + SSE 解析
        return {"content": [{"type": "text", "text": text}]}

    def _run_chat(self, message: str) -> str:
        from .bridge import ChatBridge
        return ChatBridge(self.app).call(message)