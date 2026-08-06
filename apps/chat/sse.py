# apps/chat/sse.py
"""统一 SSE 协议（Phase 4 冻结，Phase 5 引擎继续沿用）。

帧格式：data: <json>\n\n
事件类型：node_start / content_delta / tool_call / node_end / message_end
"""
import json
import queue
from dataclasses import dataclass, field
from typing import Iterator

# 事件类型常量（前后端契约，只可新增不可改名/删除）
EVT_NODE_START = "node_start"
EVT_CONTENT_DELTA = "content_delta"
EVT_TOOL_CALL = "tool_call"
EVT_NODE_END = "node_end"
EVT_MESSAGE_END = "message_end"


@dataclass
class SSEEvent:
    type: str                                   # 事件类型
    node_id: str | None = None                  # 所属节点
    node_type: str | None = None                # 节点类型（如 search-knowledge-node / ai-chat-node）
    content: str = ""                           # 增量文本（content_delta 时逐块携带）
    reasoning_content: str = ""                 # 推理内容（reasoning 模型）
    tool_calls: list[dict] = field(default_factory=list)
    usage: dict | None = None                   # token 统计，仅 message_end 一次性回传
    is_end: bool = False
    node_status: str = "SUCCESS"
    answer_text: str = ""                       # 仅 message_end 回传最终答案（Phase 5 引擎用）
    details: dict | None = None                 # 节点附加载荷（form-node 中断时携带表单/执行信息）

    def to_frame(self) -> str:
        """序列化为 SSE 帧：data: <json>\n\n"""
        return f"data: {json.dumps(self.__dict__, ensure_ascii=False)}\n\n"


class EventEmitter:
    """生产-消费解耦：引擎步骤线程 emit，StreamingHttpResponse 消费 stream()。"""

    def __init__(self):
        self._q: queue.Queue[SSEEvent | None] = queue.Queue()

    def emit(self, ev: SSEEvent) -> None:
        self._q.put(ev)

    def close(self) -> None:
        self._q.put(None)                       # 结束哨兵

    def events(self) -> Iterator[SSEEvent]:
        """事件迭代器（供 OpenAI 适配等需按对象消费的场景）。"""
        while (ev := self._q.get()) is not None:
            yield ev

    def stream(self) -> Iterator[str]:
        """帧迭代器，供 StreamingHttpResponse 使用。"""
        for ev in self.events():
            yield ev.to_frame()