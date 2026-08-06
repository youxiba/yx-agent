# apps/mcp/tests/tool_server.py
# coding=utf-8
"""联调用 mock MCP server：两个纯函数工具，stdio 传输"""
from fastmcp import FastMCP

mcp = FastMCP("maxkb-mock-tools")


@mcp.tool()
def add(a: int, b: int) -> int:
    """两数相加"""
    return a + b


@mcp.tool()
def upper(text: str) -> str:
    """字符串转大写"""
    return text.upper()


if __name__ == "__main__":
    mcp.run(transport="stdio")