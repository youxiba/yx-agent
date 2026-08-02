from .models import Role


class P:
    """全局权限点常量（前后端路由 meta 共用语义）"""
    USER_MANAGE = "user.manage"
    WORKSPACE_MANAGE = "workspace.manage"
    MODEL_READ = "model.read"
    MODEL_WRITE = "model.write"
    KNOWLEDGE_READ = "knowledge.read"
    KNOWLEDGE_WRITE = "knowledge.write"
    APPLICATION_READ = "application.read"
    APPLICATION_WRITE = "application.write"
    TOOL_READ = "tool.read"
    TOOL_WRITE = "tool.write"
    TRIGGER_READ = "trigger.read"
    TRIGGER_WRITE = "trigger.write"
    SYSTEM_MANAGE = "system.manage"


_ALL = {v for v in P.__dict__.values() if isinstance(v, str)}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    Role.ADMIN: _ALL,
    Role.WORKSPACE_MANAGE: {P.MODEL_READ, P.MODEL_WRITE, P.KNOWLEDGE_READ, P.KNOWLEDGE_WRITE,
                            P.APPLICATION_READ, P.APPLICATION_WRITE, P.TOOL_READ, P.TOOL_WRITE,
                            P.TRIGGER_READ, P.TRIGGER_WRITE, P.USER_MANAGE},
    Role.USER: {P.MODEL_READ, P.KNOWLEDGE_READ, P.APPLICATION_READ, P.TOOL_READ},
}


def get_user_permissions(user) -> set[str]:
    """角色 → 权限点集合；后续可叠加资源级权限"""
    return ROLE_PERMISSIONS.get(user.role, set())