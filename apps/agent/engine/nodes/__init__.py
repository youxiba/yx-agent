# coding=utf-8
"""节点装配：启动时注册全部内置节点（后续各 Day 增量追加 import + register）。"""
from agent.engine.registry import NODES
from agent.engine.nodes.condition_node import ConditionNode

NODES.register(ConditionNode)