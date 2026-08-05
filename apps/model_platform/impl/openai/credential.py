from ...spi import BaseCredential, ModelType


class OpenAICredential(BaseCredential):
    field_schema = [
        {"key": "api_base", "label": "API Base", "type": "text", "required": True,
         "default": "https://api.openai.com/v1"},
        {"key": "api_key", "label": "API Key", "type": "password", "required": True},
    ]

    def is_valid(self, credential: dict, model_type: ModelType, model_name: str) -> bool:
        if not credential.get("api_key"):
            return False
        try:
            from .model import OpenAIChatModel
            model = OpenAIChatModel(model_name, credential)
            model.invoke([{"role": "user", "content": "hi"}], max_tokens=1)
            return True
        except Exception:
            return False