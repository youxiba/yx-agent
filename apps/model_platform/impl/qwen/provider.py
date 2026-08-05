from model_platform import registry
from model_platform.impl.qwen.credential import QwenCredential
from model_platform.impl.qwen.model import QwenChatModel
from model_platform.models import ModelType
from model_platform.spi import ModelInfo, IModelProvider

_cred = QwenCredential()
INFOS = [ModelInfo("qwen-plus", "通义千问 Plus", ModelType.LLM, _cred, QwenChatModel)]


class QwenModelProvider(IModelProvider):
    def get_provider_info(self):
        return {"key": "qwen", "name": "Qwen", "icon": "qwen.png"}

    def get_model_list(self, model_type):
        return [i for i in INFOS if i.model_type == model_type]

    def is_valid_credential(self, model_type, model_name, credential):
        return _cred.is_valid(credential, model_type, model_name)

    def get_model(self, model_type, model_name, credential, **kw):
        info = next(i for i in INFOS if i.model_type == model_type and i.name == model_name)
        return info.model_cls(model_name, credential, **kw)


registry.register_provider("qwen", QwenModelProvider())
