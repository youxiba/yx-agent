# coding=utf-8
"""节点装配：启动时注册全部内置节点（后续各 Day 增量追加 import + register）。"""
"""节点装配：注册全部内置节点；run_workflow 注入 executor/graph 服务。"""
from agent.engine.registry import NODES
from agent.engine.nodes.condition_node import ConditionNode

from agent.engine.nodes.loop_node import LoopNode, LoopStartNode, LoopBreakNode, LoopContinueNode
NODES.register(ConditionNode)
NODES.register(LoopNode); NODES.register(LoopStartNode)
NODES.register(LoopBreakNode); NODES.register(LoopContinueNode)