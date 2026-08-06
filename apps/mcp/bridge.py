# apps/mcp/bridge.py
# coding=utf-8
"""内部会话桥接：MCP tools/call → 跑引擎 V1 线性管线 → 回答纯文本。

对应 plan Day 10；ChatBridge.call 被 test_end_to_end 打桩，真实链路在
联调清单 12.1 验证。回答只回文本，剔除 <tool_calls_render> 渲染标签。
"""
import re

from application.models import Application
from chat.engine.v1.builder import build_simple_pipeline
from chat.engine.v1.context import PipelineContext
from common.exceptions import AppApiException

_TOOL_CALL_TAG = re.compile(r"<tool_calls_render>.*?</tool_calls_render>", re.S)


class ChatBridge:
    """把一次 MCP 工具调用转成对应用的一次对话，返回回答文本。"""

    def __init__(self, app: Application, user_id=None):
        self.app, self.user_id = app, user_id

    def call(self, message: str) -> str:
        ctx = PipelineContext(
            question=message,
            chat_history=[],
            knowledge_setting=self.app.knowledge_setting,
            model_setting=self.app.model_setting,
        )
        build_simple_pipeline(self.app).run(ctx)
        text = (ctx.answer or "").strip()
        if not text:
            raise AppApiException("MCP: 应用未返回回答", code=500)
        # 剔除 <tool_calls_render> 渲染标签，只回纯文本
        return _TOOL_CALL_TAG.sub("", text)
