from model_platform import registry
from model_platform.impl.deepseek.credential import DeepSeeKCredential
from model_platform.impl.deepseek.model import DeepSeekChatModel
from model_platform.models import ModelType
from model_platform.spi import ModelInfo, IModelProvider

_cred = DeepSeeKCredential()
INFOS = [
    ModelInfo("deepseek-chat", "DeepSeek-V3", ModelType.LLM, _cred, DeepSeekChatModel),
    ModelInfo("deepseek-reasoner", "DeepSeek-R1", ModelType.LLM, _cred, DeepSeekChatModel),
]


class DeepSeekModelProvider(IModelProvider):
    def get_provider_info(self):
        return {"key": "deepseek", "name": "DeepSeek", "icon": "deepseek.png"}

    def get_model_list(self, model_type):
        return [i for i in INFOS if i.model_type == model_type]

    def is_valid_credential(self, model_type, model_name, credential):
        return _cred.is_valid(credential, model_type, model_name)

    def get_model(self, model_type, model_name, credential, **kw):
        info = next(i for i in INFOS if i.model_type == model_type and i.name == model_name)
        return info.model_cls(model_name, credential, **kw)


registry.register_provider("deepseek", DeepSeekModelProvider())
