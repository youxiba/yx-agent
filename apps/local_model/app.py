import os

from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

app = FastAPI(title="yx-local-model")

MODEL_NAME = os.environ.get("EMBEDDING_MODEL_NAME", "shibing624/text2vec-base-chinese")
_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)   # 首次调用触发下载/加载
    return _model


class EmbedQueryReq(BaseModel):
    text: str                                      # 单条查询：text（与客户端契约一致）


class EmbedDocsReq(BaseModel):
    texts: list[str]


@app.get("/health")
def health():
    return {"status": "UP", "model": MODEL_NAME}


@app.post("/model/{model_id}/embed_query")
def embed_query(model_id: str, body: EmbedQueryReq):
    vec = get_model().encode(body.text, normalize_embeddings=True)
    return {"data": vec.tolist()}


@app.post("/model/{model_id}/embed_documents")
def embed_documents(model_id: str, body: EmbedDocsReq):
    vecs = get_model().encode(body.texts, normalize_embeddings=True)
    return {"data": [v.tolist() for v in vecs]}


@app.post("/model/{model_id}/compress_documents")
def compress_documents(model_id: str, body: EmbedDocsReq):
    return {"data": body.texts}
