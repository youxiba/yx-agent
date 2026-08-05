from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from .models import ModelType


class MaxKBBaseModel(ABC):
    """所有模型类的统一基类；子类按能力实现对应方法"""
    @abstractmethod
    def stream(self, messages: list[dict], **kw) -> Any:
        """流式返回生成器: yield {"content": str, "reasoning_content": str}"""

    def invoke(self, messages: list[dict], **kw) -> str:
        return "".join(c["content"] for c in self.stream(messages, **kw))

    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class BaseCredential(ABC):
    """凭据抽象：field_schema 驱动前端表单，is_valid 做真实调用校验"""
    field_schema: list[dict] = []     # [{"key","label","type","required","default"}]

    @abstractmethod
    def is_valid(self, credential: dict, model_type: ModelType, model_name: str) -> bool: ...


@dataclass(frozen=True)
class ModelInfo:
    name: str
    desc: str
    model_type: ModelType
    credential_cls: type            # BaseCredential 子类
    model_cls: type[MaxKBBaseModel]


class IModelProvider(ABC):
    @abstractmethod
    def get_provider_info(self) -> dict: ...               # {"key","name","icon"}
    @abstractmethod
    def get_model_list(self, model_type: ModelType) -> list[ModelInfo]: ...
    @abstractmethod
    def is_valid_credential(self, model_type, model_name, credential) -> bool: ...
    @abstractmethod
    def get_model(self, model_type, model_name, credential, **kw) -> MaxKBBaseModel: ...
    def get_dialogue_number(self) -> int:
        return 3