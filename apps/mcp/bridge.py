# apps/mcp/bridge.py
# coding=utf-8
"""内部会话桥接：MCP tools/call → 建会话 → 走 Phase 4 SSE 链路 → 解析回答文本"""
import re
from apps.application.models import Application
from apps.chat.sse import EVT_CONTENT_DELTA, EVT_MESSAGE_END
from common.exceptions import AppApiException

_TOOL_CALL_TAG = re.compile(r"<tool_calls_render>.*?</tool_calls_render>", re.S)


class ChatBridge:
    def __init__(self, app: Application, user_id=None):
        self.app, self.user_id = app, user_id

    def call(self, message: str) -> str:
        """同步入口：Django 同步视图直接调用"""
        import asyncio
        return asyncio.run(self._acall(message))

    async def _acall(self, message: str) -> str:
        # 1) 建会话（Phase 4 ChatService）
        from apps.chat.services import ChatService
        chat = await ChatService.open(self.app, user_id=self.user_id)
        # 2) 复用聊天 SSE 生成器，逐事件收集回答
        buf: list[str] = []
        async for ev in ChatService.stream(chat, message):
            if ev.type == EVT_CONTENT_DELTA and ev.content:
                buf.append(ev.content)
            if ev.type == EVT_MESSAGE_END:
                break
        text = "".join(buf).strip()
        if not text:
            raise AppApiException("MCP: 应用未返回回答", code=500)
        # 3) 剔除 <tool_calls_render> 渲染标签，只回纯文本
        return _TOOL_CALL_TAG.sub("", text)