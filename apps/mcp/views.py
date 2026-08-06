# apps/mcp/views.py
# coding=utf-8
"""MCP JSON-RPC 端点路由分发"""
import json
from django.http import JsonResponse
from rest_framework.views import APIView
from .server import MCPToolHandler
from common.exceptions import AppApiException

METHODS = ("initialize", "tools/list", "tools/call")


def rpc_error(code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": None, "error": {"code": code, "message": message}}


class McpEndpointView(APIView):
    authentication_classes = []          # 认证由 handler 内部做（Bearer app-key）
    permission_classes = []

    def post(self, request):
        try:
            body = json.loads(request.body or b"{}")
        except json.JSONDecodeError:
            return JsonResponse(rpc_error(-32700, "parse error"))
        method = body.get("method")
        if body.get("jsonrpc") != "2.0" or method not in METHODS:
            return JsonResponse(rpc_error(-32601, "method not found"))
        try:
            token = (request.headers.get("Authorization") or "").removeprefix("Bearer ").strip()
            handler = MCPToolHandler(token)
            fn = {"initialize": handler.initialize,
                  "tools/list": handler.list_tools,
                  "tools/call": lambda: handler.call_tool(body.get("params") or {})}.get(method)
            result = fn()
        except AppApiException as e:
            return JsonResponse(rpc_error(-32000, e.message))
        except Exception as e:           # 兜底：不把内部堆栈暴露给调用方
            return JsonResponse(rpc_error(-32603, f"internal error: {type(e).__name__}"))
        return JsonResponse({"jsonrpc": "2.0", "id": body.get("id"), "result": result})