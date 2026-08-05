from model_platform.impl.openai.model import OpenAIChatModel


class DeepSeekChatModel(OpenAIChatModel):
    def __init__(self, model_name,credential,**kw):
        super().__init__(model_name,{**credential,
                                     "api_base":credential("api_base") or "https://api.deepseek.com"},**kw)

