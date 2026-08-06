# apps/chat/tests/fake_gateway.py
"""测试用 fake：可编程的 gateway 与流式模型，便于断言事件序列。"""


class FakeModel:
    def __init__(self, chunks=None, usage=None):
        self.chunks = chunks or [{"content": "你", "reasoning_content": ""},
                                 {"content": "好", "reasoning_content": "（推理）"}]
        self.last_usage = usage or {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}

    def stream(self, messages):
        for c in self.chunks:
            yield c

    def invoke(self, messages):
        return {"content": "".join(c.get("content", "") for c in self.chunks)}


class FakeGateway:
    def __init__(self, chunks=None):
        self.model = FakeModel(chunks)

    def get_model(self, model_id):
        return self.model