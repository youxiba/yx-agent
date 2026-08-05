from model_platform.impl.ollama.credential import OllamaCredential
from model_platform.impl.ollama.model import OllamaChatModel
from model_platform.models import ModelType
from model_platform.registry import register_provider
from model_platform.spi import ModelInfo, IModelProvider

_cred = OllamaCredential()
INFOS = [ModelInfo("qwen2.5:7b", "Qwen2.5 7B（Ollama）", ModelType.LLM, _cred, OllamaChatModel)]


class OllamaModelProvider(IModelProvider):
    def get_provider_info(self):
        return {"key": "ollama", "name": "Ollama", "icon": "ollama.png"}

    def get_model_list(self, model_type):
        return [i for i in INFOS if i.model_type == model_type]

    def is_valid_credential(self, model_type, model_name, credential):
        return _cred.is_valid(credential, model_type, model_name)

    def get_model(self, model_type, model_name, credential, **kw):
        info = next(i for i in INFOS if i.model_type == model_type and i.name == model_name)
        return info.model_cls(model_name, credential, **kw)


register_provider("ollama", OllamaModelProvider())
