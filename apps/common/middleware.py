import re

from django.http import JsonResponse
from django.utils.timezone import now
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from common.cache import cache_get

# 公开免认证路径（登录/刷新不需要 token）
PUBLIC_PATHS = ("/api/admin/auth/login", "/api/admin/auth/refresh")

# 路径前缀 -> 认证策略
PATH_POLICY = [
    (r"^/api/admin/", "jwt"),
    (r"^/api/public/", "optional"),
    (r"^/api/chat/", "chat"),
]


def resolve_policy(path: str) -> str:
    for pat, policy in PATH_POLICY:
        if re.match(pat, path):
            return policy
    return "reject"


def _unauthorized(msg="未认证"):
    return JsonResponse({"code": 401, "message": msg, "data": None}, status=401)


class AuthenticationMiddleware:
    """JWT 认证中间件：按路径策略校验 Bearer token"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.auth_policy = resolve_policy(request.path)
        request.user = None
        request.auth = None

        # 登录/刷新等公开路径，跳过 JWT 校验
        if request.path.startswith(PUBLIC_PATHS):
            return self.get_response(request)

        if request.auth_policy == "jwt":
            auth = request.headers.get("Authorization", "")
            token = auth.removeprefix("Bearer ").strip()

            # 应用 Key（app-key-*）：按哈希查 ApiKey 表
            if token.startswith("app-key-"):
                from identity.services import ApiKeyService
                ak = ApiKeyService.authenticate(token)
                if not ak or (ak.expires_at and ak.expires_at < now()):
                    return _unauthorized("应用 Key 无效或已过期")
                request.user = ak.user
                request.auth = {"type": "api_key", "ak_id": str(ak.id)}
                return self.get_response(request)

            # JWT 用户
            if not token:
                return _unauthorized("缺少 Authorization 头")
            try:
                validated = JWTAuthentication().get_validated_token(token)
                user = JWTAuthentication().get_user(validated)
                if cache_get(f"jwt:blacklist:{validated['jti']}"):
                    return _unauthorized("token 已注销")
                request.user = user
                request.auth = validated
            except (InvalidToken, TokenError):
                return _unauthorized("token 无效或已过期")

        return self.get_response(request)
