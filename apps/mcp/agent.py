# apps/mcp/agent.py
# coding=utf-8
"""deepagents 子流程运行器：create_deep_agent + MemorySaver + SandboxShellBackend。

仅本 Phase 允许引入 langgraph/deepagents（见基线约定）。
"""
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from deepagents import create_deep_agent

from chat.sse import SSEEvent, EVT_CONTENT_DELTA, EVT_TOOL_CALL
from mcp.backend import SandboxShellBackend


class DeepAgentRunner:
    def __init__(self, model, tools, *, thread_id: str = "", emitter=None):
        self.model, self.tools = model, tools
        self.emitter = emitter
        self.thread_id = thread_id
        self.tool_calls: list[dict] = []
        self.agent = create_deep_agent(
            model=model,
            backend=SandboxShellBackend(),                    # 禁真实 shell（安全红线）
            tools=tools,
            checkpointer=MemorySaver(),                       # thread_id=chat_id 隔离多轮
            interrupt_on={"write_file": False, "read_file": False, "edit_file": False},
        )
        self.config = {"configurable": {"thread_id": thread_id or "default"}}

    async def arun(self, messages: list) -> str:
        """异步主入口：astream 输出流式渲染到 EventEmitter，返回最终回答文本"""
        final = []
        async for event in self.agent.astream({"messages": messages},
                                              self.config, stream_mode="updates"):
            for update in event.values():
                if not update:                    # updates 模式某些节点产 None 帧
                    continue
                msgs = update.get("messages", [])
                for m in msgs:
                    if isinstance(m, AIMessage):
                        for tc in (m.tool_calls or []):
                            self.tool_calls.append(tc)
                            if self.emitter:
                                self.emitter.emit(SSEEvent(EVT_TOOL_CALL, content=tc["name"]))
                        if m.content:
                            final.append(m.content)
                            if self.emitter:
                                self.emitter.emit(SSEEvent(EVT_CONTENT_DELTA, content=m.content))
        return "".join(final)

    def run(self, messages: list) -> str:
        """同步桥接：Django 同步视图/节点无法 await 时使用（内部起临时事件循环）"""
        import asyncio
        return asyncio.run(self.arun(messages))