# apps/chat/tests/test_chat_step.py
"""ChatStep 流式事件序列断言（用 fake 模型，无外部依赖）。"""
import json
from chat.engine.v1.context import PipelineContext
from chat.engine.v1.steps.chat_step import ChatStep
from chat.sse import EventEmitter
from .fake_gateway import FakeGateway


def test_chat_step_emits_delta_and_end():
    em = EventEmitter()
    ctx = PipelineContext(question="你好", model_setting={"model_id": "m1"}, emitter=em)
    ChatStep(gateway=FakeGateway()).execute(ctx)
    em.close()
    frames = list(em.stream())
    types = [json.loads(f[6:])["type"] for f in frames]
    # node_start + 内容delta(你) + 内容delta(好) + 推理delta + node_end + message_end
    assert types == ["node_start", "content_delta", "content_delta", "content_delta",
                     "node_end", "message_end"]
    last = json.loads(frames[-1][6:])
    assert last["is_end"] is True and last["usage"]["total_tokens"] == 7
    assert ctx.answer == "你好"
    assert ctx.reasoning_content == "（推理）"


def test_chat_step_directly_return_skips_llm():
    em = EventEmitter()
    ctx = PipelineContext(question="q", model_setting={"model_id": "m1"},
                          paragraph_list=[{"content": "直接命中内容", "similarity": 0.95}],
                          directly_return=True, emitter=em)
    ChatStep(gateway=FakeGateway()).execute(ctx)
    em.close()
    assert ctx.answer == "直接命中内容"
    assert list(em.stream()) == []       # 直接返回不产生任何流式事件