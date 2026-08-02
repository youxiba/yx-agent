from django.contrib.auth import authenticate

from common.cache import cache_set
from common.exceptions import AppApiException
from identity.models import User, Workspace, Role, WorkspaceMember


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
