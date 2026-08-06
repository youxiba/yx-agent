import secrets
import time
from django_redis import get_redis_connection


class redis_lock:
    """基于 Redis SET NX EX 的互斥锁上下文管理器，用于定时任务防重复执行。

    用法:
        with redis_lock("trigger:xxx", timeout=120):
            ...
    特性: 带 token 的释放（Lua 原子校验），杜绝误删他人持有的锁。
    """

    def __init__(self, key: str, timeout: int = 60, wait: float = 0.2, max_wait: float = 10.0):
        self._key = f"lock:{key}"
        self._token = secrets.token_hex(8)
        self._timeout = timeout
        self._wait = wait
        self._max_wait = max_wait

    def __enter__(self):
        client = get_redis_connection("default")
        deadline = time.monotonic() + self._max_wait
        while True:
            if client.set(self._key, self._token, nx=True, ex=self._timeout):
                return self
            if time.monotonic() >= deadline:
                raise TimeoutError(f"获取锁超时: {self._key}")
            time.sleep(self._wait)

    def __exit__(self, exc_type, exc, tb):
        client = get_redis_connection("default")
        # 仅当锁内 token 匹配才删除，防止 A 超时后误删 B 的锁
        client.eval(
            "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end",
            1, self._key, self._token,
        )