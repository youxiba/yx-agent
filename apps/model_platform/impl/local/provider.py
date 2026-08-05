from model_platform.impl.local.credential import LocalCredential
from model_platform.impl.local.model import LocalEmbeddingModel
from model_platform.models import ModelType
from model_platform.registry import register_provider
from model_platform.spi import ModelInfo, IModelProvider

_cred = LocalCredential()
INFOS = [ModelInfo("shibing624/text2vec-base-chinese", "本地中文 Embedding",
                   ModelType.EMBEDDING, _cred, LocalEmbeddingModel)]


class LocalModelProvider(IModelProvider):
    def get_provider_info(self):
        return {"key": "local", "name": "本地模型", "icon": "local.png"}

    def get_model_list(self, model_type):
        return [i for i in INFOS if i.model_type == model_type]

    def is_valid_credential(self, model_type, model_name, credential):
        return _cred.is_valid(credential, model_type, model_name)

    def get_model(self, model_type, model_name, credential, **kw):
        info = next(i for i in INFOS if i.model_type == model_type and i.name == model_name)
        return info.model_cls(model_name, credential, **kw)


register_provider("local", LocalModelProvider())
