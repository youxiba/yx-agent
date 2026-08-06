# coding=utf-8
from model_platform.service.gateway import gateway   # Phase 2 单例：本地模型已封装为 local_model 微服务


class EmbeddingService:
    """统一 embedding 入口：批量调用 ModelGateway 取向量（一次网络往返）"""

    def embed_query(self, model_id: str, text: str) -> list[float]:
        return gateway.get_model(model_id).embed_query(text)

    def embed_documents(self, model_id: str, texts: list[str]) -> list[list[float]]:
        return gateway.get_model(model_id).embed_documents(texts)