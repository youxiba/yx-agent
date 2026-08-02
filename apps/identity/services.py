import hashlib
import secrets

from django.contrib.auth import authenticate

from common.cache import cache_set
from common.exceptions import AppApiException
from identity.models import User, Workspace, Role, WorkspaceMember, ApiKey


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


class WorkspaceService:
    @staticmethod
    def create(name: str, owner) -> Workspace:
        ws = Workspace.objects.create(name=name, owner=owner)
        WorkspaceMember.objects.create(workspace=ws, user=owner, role=Role.WORKSPACE_MANAGE)
        return ws

    @staticmethod
    def ensure_member(ws: Workspace, user: User) -> WorkspaceMember:
        m = WorkspaceMember.objects.filter(workspace=ws, user=user).first()
        if m is None:
            raise AppApiException("你不是该工作空间成员", code=403)
        return m

    @staticmethod
    def require_owner_or_manage(ws: Workspace, user: User) -> None:
        m = WorkspaceService.ensure_member(ws, user)
        if m.role not in (Role.WORKSPACE_MANAGE, Role.ADMIN):
            raise AppApiException("需要工作空间管理权限", code=403)

class ApiKeyService:
    @staticmethod
    def _hash(key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def create(user, name: str, scope: str) -> dict:
        """返回明文 key 只展示一次  ，库中只存hash"""
        plain = f"app-key-{secrets.token_urlsafe(32)}"
        ak = ApiKey.objects.create(user=user, name=name, scope=scope,key_hash=ApiKeyService._hash(plain))
        return {"id": ak.id,"key":plain}

    @staticmethod
    def authenticate(token: str) -> ApiKey | None:
        if not token.startswith("app-key-"):
            return None
        return ApiKey.objects.filter(key_hash=ApiKeyService._hash(token),is_active=True).first()