import re
from tokenize import TokenError

from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from common.cache import cache_get

#路径前缀-》认证策略
PATP_POLICY = [
    (r"^/api/admin/","jwt"),
    (r"^/api/public/","optional"),
    (r"^/api/chat/","chat"),
]

def resolve_policy(path: str) -> str:
    for pat,policy in PATP_POLICY:
        if re.match(pat,path):
            return policy
        return "reject"

def _unauthorized(msg = "未认证"):
    return JsonResponse({"code":401,"message":msg,"data":None},status=401)

class AuthenticationMiddleware:
    """占位骨架，先全部放行"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.auth_policy = resolve_policy(request.path)
        request.user =  None
        request.auth = None

        if request.auth_policy == "jwt":
            auth = request.headers.get("Authorization","")
            token = auth.removeprefix("Bearer ").strip()
            if not token:
                return _unauthorized("缺少 Authorization头")
            try:
                validated,user = JWTAuthentication().get_user(JWTAuthentication().get_validated_token(token))
                if cache_get(f"jwt.blacklist:{validated['jti']}"):
                    return _unauthorized("token 已注销")
                request.user = user
                request.auth = validated

            except (InvalidToken,TokenError):
                return _unauthorized("token 无效或已过期")

            return self.get_response(request)
























