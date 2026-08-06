# 在既有 NODES 注册清单里追加
from agent.engine.registry import NODES
from .nodes.tool_node import ToolNode
from .nodes.tool_lib_node import ToolLibNode

for cls in (ToolNode, ToolLibNode):
    NODES.register(cls)