from rest_framework.authentication import BaseAuthentication


class MiddlewareUserAuthentication(BaseAuthentication):
    """复用 AuthenticationMiddleware 已解析的用户。

    中间件在 Django 请求上设置 request.user，但 DRF 的 Request.user 是属性，
    会触发 DRF 自身的认证流程（默认空 authenticator -> AnonymousUser），
    覆盖掉中间件的结果。此类把中间件已认证的用户透传给 DRF，保证 request.user 一致。
    """

    def authenticate(self, request):
        django_request = getattr(request, "_request", request)
        user = getattr(django_request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            return user, getattr(django_request, "auth", None)
        return None
