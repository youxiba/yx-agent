from openai import OpenAI

from model_platform.spi import MaxKBBaseModel


class OpenAIChatModel(MaxKBBaseModel):
    def __init__(self, model_name: str, credential: dict, **kw):
        self.model_name = model_name
        self.kw = {k: v for k, v in kw.items() if k in ("temperature", "max_tokens", "top_p")}
        self.client = OpenAI(base_url=credential.get("api_base") or "https://api.openai.com/v1",
                             api_key=credential.get("api_key"))

    def stream(self, messages, **kw):
        stream = self.client.chat.completions.create(
            model=self.model_name, messages=messages, stream=True, **{**self.kw, **kw})
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            yield {"content": getattr(delta, "content", None) or "",
                   "reasoning_content": getattr(delta, "reasoning_content", None) or ""}


class OpenAIEmbeddingModel(MaxKBBaseModel):
    def __init__(self, model_name: str, credential: dict, **kw):
        self.model_name = model_name
        self.client = OpenAI(base_url=credential.get("api_base") or "https://api.openai.com/v1",
                             api_key=credential.get("api_key"))

    def embed_query(self, text):
        return self.embed_documents([text])[0]

    def embed_documents(self, texts):
        resp = self.client.embeddings.create(model=self.model_name, input=texts)
        return [d.embedding for d in resp.data]
