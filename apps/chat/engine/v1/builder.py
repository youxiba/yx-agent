# apps/chat/engine/v1/builder.py
"""Pipeline 工厂：为 Phase 5 引擎 V2 保留统一构建形态。"""
from application.models import Application
from model_platform.service.gateway import gateway      # Phase 2 ModelGateway 全局实例
from .pipeline import Pipeline
from .steps.reset_problem_step import ResetProblemStep
from .steps.search_knowledge_step import SearchKnowledgeStep
from .steps.build_messages_step import BuildMessagesStep
from .steps.chat_step import ChatStep


def build_simple_pipeline(app: Application) -> Pipeline:
    """应用 → 线性流水线（问题优化 → 检索 → 拼消息 → LLM 流式）。"""
    return Pipeline([
        ResetProblemStep(),
        SearchKnowledgeStep(),
        BuildMessagesStep(),
        ChatStep(gateway=gateway),
    ])