from django.core.cache import cache

def cache_get(key): return cache.get(key)
def cache_set(key, val, ttl = None): cache.set(key, val, ttl)
def cache_delete(key): cache.delete(key)
def cache_incr(key: str, delta: int = 1, ttl: int | None = None) -> int:
    """原子自增；key 不存在时初始化为 delta。"""
    try:
        return cache.incr(key, delta)
    except ValueError:                        # key 不存在，django-redis 抛 ValueError
        cache.set(key, delta, ttl)
        return delta