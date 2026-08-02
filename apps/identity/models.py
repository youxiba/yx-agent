import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "ADMIN", "管理员"
    WORKSPACE_MANAGE = "WORKSPACE_MANAGE", "工作空间管理员"
    USER = "USER", "普通用户"


class User(AbstractUser):
    """RBAC 用户：username/password 沿用 AbstractUser，权限点由自建权限表给出"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, default="")
    nick_name = models.CharField(max_length=150, blank=True, default="")
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.USER)
    source = models.CharField(max_length=16, default="LOCAL")
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    groups = None                      # 不用 Django 内置分组
    user_permissions = None            # 不用 Django 内置权限
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "user"


class Workspace(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_workspaces")
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workspace"


class WorkspaceMember(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.USER)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "workspace_member"
        constraints = [models.UniqueConstraint(fields=["workspace", "user"], name="uniq_ws_member")]


class ApiKey(models.Model):
    class Scope(models.TextChoices):
        APPLICATION = "application", "应用 Key"
        PLATFORM = "platform", "平台 Key"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")
    name = models.CharField(max_length=128)
    key_hash = models.CharField(max_length=64, db_index=True)     # 只存 sha256
    scope = models.CharField(max_length=32, choices=Scope.choices, default=Scope.APPLICATION)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "api_key"