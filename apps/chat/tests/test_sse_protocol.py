# apps/chat/tests/test_sse_protocol.py
import json
from chat.sse import EVT_CONTENT_DELTA, EVT_MESSAGE_END, EVT_NODE_START, EventEmitter, SSEEvent


def test_to_frame():
    ev = SSEEvent(type=EVT_CONTENT_DELTA, content="你好", node_type="ai-chat-node")
    frame = ev.to_frame()
    assert frame.startswith("data: ") and frame.endswith("\n\n")
    payload = json.loads(frame[6:].strip())
    assert payload["type"] == "content_delta"
    assert payload["content"] == "你好"


def test_emitter_sequence():
    em = EventEmitter()
    em.emit(SSEEvent(EVT_NODE_START, node_type="search-knowledge-node"))
    em.emit(SSEEvent(EVT_CONTENT_DELTA, content="a"))
    em.emit(SSEEvent(EVT_CONTENT_DELTA, content="b"))
    em.emit(SSEEvent(EVT_MESSAGE_END, usage={"total_tokens": 10}, is_end=True))
    em.close()
    frames = list(em.stream())
    types = [json.loads(f[6:])["type"] for f in frames]
    assert types == ["node_start", "content_delta", "content_delta", "message_end"]
    assert json.loads(frames[-1][6:])["is_end"] is True