# apps/chat/openai_adapter.py
"""内部 SSEEvent → OpenAI ChatCompletionChunk 帧适配。"""
import json
import time
import uuid

from .sse import EVT_CONTENT_DELTA, EVT_MESSAGE_END, EVT_TOOL_CALL, SSEEvent


class OpenAIToResponseAdapter:
    """把引擎发出的 SSEEvent 流转换为 OpenAI /v1/chat/completions 流式帧。"""

    def __init__(self, model_name: str = "maxkb"):
        self._model = model_name
        self._id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        self._created = int(time.time())
        self._finished = False

    def start_frame(self) -> dict:
        """首帧：空 delta + role=assistant。"""
        return self._frame({"role": "assistant", "content": ""}, finish_reason=None)

    def convert(self, ev: SSEEvent) -> dict | None:
        """SSEEvent → 一个 OpenAI chunk；node_start/node_end 不透传；message_end 出收尾帧。"""
        if ev.type == EVT_MESSAGE_END:
            if self._finished:
                return None                             # 只发一次收尾帧
            self._finished = True
            return self._frame({"content": ""}, finish_reason="stop",
                               usage=ev.usage or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
        if ev.type == EVT_CONTENT_DELTA:
            delta = {}
            if ev.content:
                delta["content"] = ev.content
            if ev.reasoning_content:
                delta["reasoning_content"] = ev.reasoning_content
            return self._frame(delta) if delta else None
        if ev.type == EVT_TOOL_CALL:
            return self._frame({"tool_calls": ev.tool_calls})
        return None                                     # node_start/node_end：内部进度，对 OpenAI 不可见

    def _frame(self, delta: dict, finish_reason=None, usage=None) -> dict:
        chunk = {
            "id": self._id,
            "object": "chat.completion.chunk",
            "created": self._created,
            "model": self._model,
            "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
        }
        if usage:
            chunk["usage"] = usage
        return chunk

    @staticmethod
    def frame_to_sse(chunk: dict) -> str:
        """OpenAI chunk → SSE 帧（data: {...}\n\n；结束时另发 data: [DONE]）。"""
        return f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"