from .models import ModelType
from .spi import ModelInfo, IModelProvider


class ModelInfoManage:
    def __init__(self, infos: list[ModelInfo] | None = None, default: dict[ModelType, ModelInfo] | None = None):
        self._infos: dict[ModelType, list[ModelInfo]] = {}
        self._default = default or {}
        for info in infos or []:
            self._infos.setdefault(info.model_type, []).append(info)

    def get_list(self, model_type: ModelType) -> list[ModelInfo]:
        return self._infos.get(model_type, [])

    def get(self, model_type: ModelType, name: str) -> ModelInfo:
        for info in self._infos.get(model_type, []):
            if info.name == name:
                return info
        return self._default[model_type]       # 精确 → 默认回退


PROVIDERS: dict[str, IModelProvider] = {}     # 各厂商模块在 apps.ready() 时注册


def register_provider(key: str, provider: IModelProvider) -> None:
    PROVIDERS[key] = provider