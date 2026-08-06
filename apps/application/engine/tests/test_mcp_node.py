# coding=utf-8
"""mcp-node 与 mock MCP server 联调：工具映射 + 多轮调用"""
import pytest


@pytest.mark.asyncio
async def test_mcp_node_calls_mock_server():
    from apps.application.engine.nodes.mcp_node import McpNode
    from apps.application.engine.node import NodeContext
    from apps.application.engine.context import ContextStore

    cfg = {
        "model_id": "<一个可用 LLM model_id>",
        "mcp_servers": {"mock": {"command": "python",
                                 "args": ["apps/mcp/tests/tool_server.py"],
                                 "transport": "stdio"}},
        "messages_field": "chat.messages",
    }
    store = ContextStore()
    store.chat_vars["messages"] = [("human", "请用 upper 工具把 hello 转大写，再用 add 算 1+2")]
    ctx = NodeContext(node_id="n1", config=cfg, store=store, chat_id=None, emitter=None)
    result = await McpNode().execute(ctx)
    assert result.node_vars["answer"]          # 最终回答非空
    names = {tc["name"] for tc in result.node_vars["tool_calls"]}
    assert "upper" in names and "add" in names