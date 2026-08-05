from model_platform.impl.openai.credential import OpenAICredential
from model_platform.models import ModelType
from model_platform.spi import ModelInfo, IModelProvider
from model_platform.registry import register_provider
from .model import OpenAIChatModel, OpenAIEmbeddingModel

_cred = OpenAICredential()
INFOS = [
    ModelInfo("gpt-4o", "GPT-4o", ModelType.LLM, _cred, OpenAIChatModel),
    ModelInfo("gpt-4o-mini", "GPT-4o mini", ModelType.LLM, _cred, OpenAIChatModel),
    ModelInfo("gpt-3.5-turbo", "GPT-3.5 Turbo", ModelType.LLM, _cred, OpenAIChatModel),
    ModelInfo("text-embedding-3-small", "text-embedding-3-small", ModelType.EMBEDDING, _cred, OpenAIEmbeddingModel),
]


class OpenAIModelProvider(IModelProvider):
    def get_provider_info(self):
        return {"key": "openai", "name": "OpenAI", "icon": "openai.png"}

    def get_model_list(self, model_type):
        return [i for i in INFOS if i.model_type == model_type]

    def is_valid_credential(self, model_type, model_name, credential):
        return _cred.is_valid(credential, model_type, model_name)

    def get_model(self, model_type, model_name, credential, **kw):
        info = next(i for i in INFOS if i.model_type == model_type and i.name == model_name)
        return info.model_cls(model_name, credential, **kw)


register_provider("openai", OpenAIModelProvider())
