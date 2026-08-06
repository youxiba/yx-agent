# coding=utf-8
from common.exceptions import AppApiException
from identity.services import WorkspaceService
from ..models import Knowledge


def get_knowledge(request, knowledge_id) -> Knowledge:
    """资源级隔离：知识库存在 + 当前用户是该 workspace 成员"""
    k = Knowledge.objects.select_related("workspace").filter(id=knowledge_id).first()
    if k is None:
        raise AppApiException("知识库不存在", code=404)
    WorkspaceService.ensure_member(k.workspace, request.user)
    return k