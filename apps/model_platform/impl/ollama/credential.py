from model_platform.impl.ollama.model import OllamaChatModel
from model_platform.spi import BaseCredential


class OllamaCredential(BaseCredential):
    field_schema = [{"key": "api_base", "label": "Ollama 地址", "type": "text", "required": True,
                     "default": "http://127.0.0.1:11434"}]

    def is_valid(self, credential,model_type,model_name):
        try:
            OllamaChatModel(model_name,credential).invoke([{"role":"user","content":"hi"}],max_tokens= 1)
            return True
        except Exception as e:
            return False