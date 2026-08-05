import json
import threading
from collections import defaultdict

from common.cache import cache, cache_set, cache_get, cache_delete
from model_platform.infra import cipher
from model_platform.infra.repos import ModelRepository
from model_platform.registry import PROVIDERS


class ModelGateway:
    def __init__(self, repo: ModelRepository):
        self.repo = repo
        self._locks = dict[str, threading.Lock] = defaultdict(threading.Lock)

    def _decrypy_cred(self, row) ->dict:
        return json.loads(cipher.decypt(row.credential))

    def get_model(self,model_id:str, *, refresh: bool = False) :
        key = f"model:{model_id}"
        if not refresh  and (m:=cache.get(key)) :
            return m
        with self._locks[model_id] :
            if not refresh  and (m := cache.cache_get(key)) :
                return m
            row = self.repo.get(model_id)
            cred = self._decrypy_cred(row)
            model = PROVIDERS[row.provider].get_model(row.model_type,row.model_name,cred,**row.model_params)
            if row.is_cacheable:
                cache_set(key,model,ttl=8*3600)
                return model

    def test(self,row) -> bool:
        cred = self._decrypy_cred(row)
        return PROVIDERS[row.provider].is_valid_credential(row.model_type,row.model_name,cred)

    def invalidate(self, model_id:str) -> None:
        cache_delete(f"model:{model_id}")


# 单例：repo 当前绑定 （比v1的repo = None） 更稳，避免启动即崩
gateway = ModelGateway(ModelRepository())

