# tests/test_ai_chat_node.py
import json
import pytest

from agent.tests.util import _mk_ctx
from chat.sse import EventEmitter, EVT_CONTENT_DELTA, EVT_NODE_START, EVT_NODE_END, EVT_MESSAGE_END
from agent.engine.graph import WorkflowGraph, GraphNode, GraphEdge
from agent.engine.executor import Executor
from agent.engine.context import ContextStore
from agent.engine.registry import NODES
from agent.engine.nodes import *


class Chunk:
    def __init__(self, text, reasoning=""): self.text, self.reasoning_content = text, reasoning


class StreamModel:
    last_usage = {"prompt_tokens": 10, "completion_tokens": 5}
    def stream(self, messages):
        for piece in ["你", "好", "！"]:
            yield Chunk(piece)


class FakeGateway:
    def get_model(self, model_id): return StreamModel()


def test_ai_chat_streams_deltas_and_usage():
    g = WorkflowGraph()
    g.add_node(GraphNode("s", "start-node", "开始"))
    g.add_node(GraphNode("a", "ai-chat-node", "对话",
                         config={"model_id": "m1", "prompt": "{{ chat.question }}"}))
    g.add_edge(GraphEdge("s", "a"))
    store = ContextStore(); store.chat_vars["question"] = "你好"
    store.chat_vars["chat_history"] = [{"role": "user", "content": "之前聊过"}]
    em = EventEmitter()
    Executor(g).run(_mk_ctx(store, em, services={"gateway": FakeGateway()}), em, "s")
    em.close()   # 结束哨兵，否则 stream() 一直阻塞
    frames = [json.loads(f[6:]) for f in em.stream()]   # 帧格式 data: {json}\n\n，剥前缀
    deltas = [f["content"] for f in frames if f["type"] == EVT_CONTENT_DELTA]
    assert "".join(deltas) == "你好！"
    assert store.resolve("global.answer") == "你好！"
    assert store.resolve("global.usage")["completion_tokens"] == 5