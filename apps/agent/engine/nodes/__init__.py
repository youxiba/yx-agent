# coding=utf-8
"""节点装配：启动时注册全部内置节点（后续各 Day 增量追加 import + register）。"""
from agent.engine.nodes.document_node import DocumentExtractNode, DocumentSplitNode, KnowledgeWriteNode
from agent.engine.nodes.search_node import SearchKnowledgeNode, SearchDocumentNode, RerankerNode

"""节点装配：注册全部内置节点；run_workflow 注入 executor/graph 服务。"""
from agent.engine.registry import NODES
from agent.engine.nodes.condition_node import ConditionNode
from agent.engine.nodes.start_node import StartNode
from agent.engine.nodes.reply_node import ReplyNode
from agent.engine.nodes.ai_chat_node import AiChatNode

NODES.register(StartNode); NODES.register(ReplyNode)

from agent.engine.nodes.loop_node import LoopNode, LoopStartNode, LoopBreakNode, LoopContinueNode
NODES.register(ConditionNode)
NODES.register(LoopNode); NODES.register(LoopStartNode)
NODES.register(LoopBreakNode); NODES.register(LoopContinueNode)
NODES.register(StartNode); NODES.register(ReplyNode)
NODES.register(AiChatNode)
NODES.register(SearchKnowledgeNode)
NODES.register(SearchDocumentNode)
NODES.register(RerankerNode)
NODES.register(DocumentExtractNode)
NODES.register(DocumentSplitNode)
NODES.register(KnowledgeWriteNode)