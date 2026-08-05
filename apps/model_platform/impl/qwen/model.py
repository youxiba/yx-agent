from model_platform.impl.openai.model import OpenAIChatModel


class QwenChatModel(OpenAIChatModel):
    def __init__(self,model_name,credential,**kw):
        super().__init__(model_name,{**credential,
                                     "api_base":credential.get("api_base")
                                     or "https://dashscope.aliyuncs.com/compatible-mode/v1"},**kw)

