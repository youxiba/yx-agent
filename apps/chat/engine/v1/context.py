# apps/chat/engine/v1/context.py
from dataclasses import dataclass, field
from chat.sse import EventEmitter


@dataclass
class PipelineContext:
    """线性流水线共享上下文（引擎 V1；Phase 5 V2 复刻此形态）。"""
    question: str                                       # 原始问题
    chat_history: list[dict] = field(default_factory=list)      # [{"role","content"}, ...]
    # 应用配置快照（进入管线即固定，避免执行中途应用配置变更造成漂移）
    knowledge_setting: dict = field(default_factory=dict)
    model_setting: dict = field(default_factory=dict)
    emitter: EventEmitter | None = None                 # 步骤向外部发流式事件
    # 步骤间传递产物
    optimized_question: str = ""                        # ResetProblem 产物
    paragraph_list: list[dict] = field(default_factory=list)    # SearchKnowledge 产物
    messages: list[dict] = field(default_factory=list)          # BuildMessages 产物
    directly_return: bool = False                       # 命中直接返回（跳过 LLM）
    answer: str = ""                                    # 最终答案
    reasoning_content: str = ""
    usage: dict | None = None
    source: list[dict] = field(default_factory=list)    # 命中知识来源
    details: dict = field(default_factory=dict)