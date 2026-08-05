import requests

from model_platform.spi import MaxKBBaseModel


class LocalEmbeddingModel(MaxKBBaseModel):
    """本地embedding :走local_model 微服务http"""
    def __init__(self, model_name,credential, **kw):
        proto = credential.get("protocol") or "http"
        host = credential.get("host") or "127.0.0.1"
        port = credential.get("port") or 11636
        self.base = f"{proto}://{host}:{port}"
        self.model_id = model_name

    def embed_query(self, text):
        return self._post("/embed_query",{"text":text})["data"]

    def embed_document(self, texts):
        return self._post("/embed_documents",{"texts":texts})["data"]

    def _post(self,path,body):
        resp = requests.post(f"{self.base}/model/{self.model_id}{path}",json=body,timeout=60)
        resp.raise_for_status()
        return resp.json()
