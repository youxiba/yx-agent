import re

#路径前缀-》认证策略
PATP_POLICY = [
    (r"^/api/admin/","jwt"),
    (r"^/api/public/","optional"),
]

def resolve_policy(path: str) -> str:
    for pat,policy in PATP_POLICY:
        if re.match(pat,path):
            return policy
        return "reject"

class AuthenticationMiddleware:
    """占位骨架，先全部放行"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.auth_policy = resolve_policy(request.path)
        request.user =  None
        request.auth = None
        return self.get_response(request)























