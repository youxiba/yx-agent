# apps/application/engine/nodes/mcp_node.py
# coding=utf-8
"""mcp-node：连接外部 MCP server，工具映射为工作流可用工具，交给 deepagents 子流程驱动。

注意：本节点 execute 为 async。Phase 5 引擎的 Executor 需在 _run_one 里检测
coroutine 并用 asyncio.run_coroutine_threadsafe 桥接到共享事件循环（见 7.3）。
"""
import asyncio
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from apps.application.engine.node import BaseNode, NodeContext, NodeResult
from apps.mcp.agent import DeepAgentRunner
from apps.model_platform.service.gateway import ModelGateway
from common.exceptions import AppApiException


class McpNode(BaseNode):
    node_type = "mcp-node"
    workflow_modes = ("application",)

    async def execute(self, ctx: NodeContext) -> NodeResult:
        config = ctx.config
        servers = config.get("mcp_servers") or {}      # {server_name: {"command"/"url", "args", "transport"}}
        model_id = config.get("model_id")
        if not servers or not model_id:
            raise AppApiException("mcp-node 需配置 mcp_servers 与 model_id", code=400)
        try:
            client = MultiServerMCPClient(servers)
            tools = await client.get_tools()
        except Exception as e:                          # 连接失败要显式报错并回滚节点
            raise AppApiException(f"MCP 连接失败: {e}", code=500)
        for t in tools:
            t.handle_tool_error = True                  # 工具异常转为消息而非中断
        messages = ctx.get_field(config.get("messages_field", "messages"))
        if not messages:
            messages = [HumanMessage(content=ctx.get_field("question") or "")]
        model = ModelGateway().get_model(model_id)
        runner = DeepAgentRunner(model, tools, thread_id=str(ctx.chat_id or ""), emitter=ctx.emitter)
        try:
            answer = await runner.arun(messages)
        except Exception as e:
            raise AppApiException(f"deepagents 子流程失败: {e}", code=500)
        await client.__aexit__(None, None, None)        # 释放连接
        return NodeResult(node_vars={"answer": answer, "tool_calls": runner.tool_calls})