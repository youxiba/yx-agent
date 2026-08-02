from django.core.cache import cache

def cache_get(key): return cache.get(key)
def cache_set(key, val, ttl = None): cache.set(key, val, ttl)
def cache_delete(key): cache.delete(key)