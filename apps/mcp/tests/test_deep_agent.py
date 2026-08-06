# coding=utf-8
"""deepagents 子流程：多轮工具调用 + MemorySaver 检查点恢复"""
from mcp.agent import DeepAgentRunner


def test_agent_uses_tools_and_checkpoints():
    """FakeChatModel 预置 tool-call 序列，无需真实 LLM/外部 MCP"""
    from mcp.tests.fakes import FakeChatModel, upper
    runner = DeepAgentRunner(FakeChatModel(), [upper], thread_id="chat-1")
    ans = runner.run([("human", "用 upper 把 hello 转大写")])
    assert "HELLO" in ans
    assert runner.tool_calls and runner.tool_calls[0]["name"] == "upper"
    # MemorySaver：同一 thread_id 二次调用仍在上文基础上继续（checkpoint 生效）
    ans2 = runner.run([("human", "刚才的结果是什么")])
    assert "HELLO" in ans2