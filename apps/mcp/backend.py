# apps/mcp/backend.py
# coding=utf-8
"""deepagents 执行后端：MCP 消费端 deep agent 的 shell 能力。

与 MaxKB-2 `application/flow/backend/sandbox_shell.py` 对齐（子类化
deepagents.backends.LocalShellBackend），但本项目尚未落地 sandbox.so /
降权运行用户，因此 execute 一律拒绝真实 shell 执行，避免工具级 RCE
（Day 8 安全红线：宁可禁掉 shell 能力）。
"""
import tempfile

from deepagents.backends import LocalShellBackend
from deepagents.backends.protocol import ExecuteResponse


class SandboxShellBackend(LocalShellBackend):
    """受限 shell 后端：文件工具可用，execute（真实 shell）一律拒绝。"""

    def __init__(self, root_dir: str | None = None, **kwargs):
        kwargs.setdefault("virtual_mode", True)
        super().__init__(root_dir=root_dir or tempfile.gettempdir(), **kwargs)

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        return ExecuteResponse(
            output="shell execution is disabled in MCP deep agent (security)",
            exit_code=1,
        )
