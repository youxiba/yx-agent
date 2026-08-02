from rest_framework_simplejwt.tokens import RefreshToken,AccessToken,TokenError

from common.exceptions import PermissionDenied


def issue_token_pair(user) -> dict:
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    return {"access":str(refresh.access_token),"refresh":str(refresh)}

def decode_access(token: str) -> dict:
    try:
        return AccessToken(token).payload
    except TokenError:
        raise PermissionDenied("token 无效或已过期")