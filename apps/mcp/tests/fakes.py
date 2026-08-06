# apps/mcp/tests/fakes.py
# coding=utf-8
"""deepagents 子流程测试替身：FakeChatModel（预置 tool-call 序列）+ upper 工具。

避免单测真调 LLM/外部 MCP：FakeChatModel 第 1 次调用返回工具调用(upper)，
第 2 次起返回文本回答，驱动 create_deep_agent 走完整「工具调用→回答」图。
"""
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool


@tool
def upper(text: str) -> str:
    """字符串转大写"""
    return text.upper()


class FakeChatModel(BaseChatModel):
    """按调用次数返回预置序列：1 → tool_calls(upper)，后续 → "HELLO"。"""

    _invocations: int = 0

    def bind_tools(self, tools, **kwargs):
        return self

    @property
    def _llm_type(self) -> str:
        return "fake-chat-model"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        self._invocations += 1
        if self._invocations == 1:
            msg = AIMessage(content="", tool_calls=[{
                "name": "upper", "args": {"text": "hello"},
                "id": "call_test_1", "type": "tool_call",
            }])
        else:
            msg = AIMessage(content="HELLO")
        return ChatResult(generations=[ChatGeneration(message=msg)])
