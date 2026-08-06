# apps/tool/tests/conftest.py
import pytest
from tool.infra.executor import ToolExecutor
from tool.infra.sandbox import SandboxConfig


@pytest.fixture
def ex():
    """每用例独立沙箱，白名单默认全禁网络，超时 10s 防卡测试"""
    return ToolExecutor(SandboxConfig(timeout=10))


@pytest.fixture
def ex_net():
    """带网络白名单的沙箱：允许连 mock 服务"""
    return ToolExecutor(SandboxConfig(timeout=10, net_allow_hosts=("127.0.0.1", "localhost")))