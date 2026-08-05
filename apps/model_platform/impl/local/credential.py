from model_platform.impl.local.model import LocalEmbeddingModel
from model_platform.spi import BaseCredential


class LocalCredential(BaseCredential):
    field_schema = [
        {"key": "host", "label": "服务地址", "type": "text", "required": True, "default": "127.0.0.1"},
        {"key": "port", "label": "端口", "type": "number", "required": True, "default": 11636},
    ]

    def is_valid(self, credential, model_type,model_name):
        try:
            LocalEmbeddingModel(model_name, credential).embed_query("hi")
            return True
        except Exception as e:
            return False

