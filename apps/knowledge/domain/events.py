# coding=utf-8
import uuid
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class DomainEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(kw_only=True)
class DocumentIngested(DomainEvent):
    """文档已入库 → 触发切分"""
    document_id: str
    knowledge_id: str


@dataclass(kw_only=True)
class ParagraphEmbedded(DomainEvent):
    """段落已向量化 → 触发全文分词"""
    document_id: str
    paragraph_ids: list[str]


class EventBus:
    """轻量进程内事件总线（异步任务仍走 Celery，事件仅做编排触发）"""
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}

    def on(self, event_type: type, handler: Callable):
        self._handlers.setdefault(event_type.__name__, []).append(handler)

    def emit(self, event: DomainEvent):
        for handler in self._handlers.get(type(event).__name__, []):
            handler(event)


bus = EventBus()