from django.contrib.auth import authenticate

from common.cache import cache_set
from common.exceptions import AppApiException
from identity.models import User


class AuthService:

    def login(username: str, password: str) -> User:
        user = authenticate(username=username, password=password)
        if user is None:
            raise AppApiException("用户名或密码错误", code=401)
        if not user.is_active:
            raise AppApiException("账号已被禁用", code=401)
        return user

    def logout(jti: str) -> None:
        cache_set(f"jwt:blacklist:{jti}", 1, ttl=86400)