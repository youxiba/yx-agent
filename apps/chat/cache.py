# apps/chat/cache.py
"""会话运行时缓存：应用配置快照 + 最近历史 + 会话元信息，全部走 Redis。"""
import json
from common.cache import cache_get, cache_set, cache_delete

INFO_KEY = "chat_info:{chat_id}"                 # 会话运行时上下文
HISTORY_KEY = "chat_info:{chat_id}:history"      # 会话最近 N 条历史（构造多轮上下文用）
HISTORY_MAX = 10                                 # 单会话上下文最多带的历史条数


class ChatInfoService:
    """以会话维度缓存运行时信息；TTL 必须设置，过期从 DB 重建。"""

    @staticmethod
    def set(chat_id: str, info: dict, ttl: int = 3600) -> None:
        cache_set(INFO_KEY.format(chat_id=chat_id), json.dumps(info, ensure_ascii=False), ttl=ttl)

    @staticmethod
    def get(chat_id: str) -> dict | None:
        raw = cache_get(INFO_KEY.format(chat_id=chat_id))
        return json.loads(raw) if raw else None

    @staticmethod
    def delete(chat_id: str) -> None:
        cache_delete(INFO_KEY.format(chat_id=chat_id))
        cache_delete(HISTORY_KEY.format(chat_id=chat_id))

    # ---- 历史记录（多轮上下文） ----
    @staticmethod
    def push_history(chat_id: str, record: dict) -> None:
        """追加 {role, content} 到历史（右进，超长裁左）。"""
        key = HISTORY_KEY.format(chat_id=chat_id)
        items = json.loads(cache_get(key) or "[]")
        items.append(record)
        items = items[-HISTORY_MAX:]
        cache_set(key, json.dumps(items, ensure_ascii=False), ttl=3600)

    @staticmethod
    def get_history(chat_id: str) -> list[dict]:
        return json.loads(cache_get(HISTORY_KEY.format(chat_id=chat_id)) or "[]")