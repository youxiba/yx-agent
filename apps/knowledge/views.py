# coding=utf-8
from rest_framework.views import APIView
from common.result import Result
from identity.permissions import P
from common.auth.decorators import require_permissions
from .services.preview import PreviewService


class ParagraphSplitView(APIView):
    """POST /api/admin/knowledge/paragraph/split  分段预览（multipart: file, limit）"""
    @require_permissions(P.KNOWLEDGE_WRITE)
    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            return Result.error("缺少上传文件", code=400)
        limit = int(request.data.get("limit", 256))
        preview = PreviewService().split(upload, limit)
        return Result.success({"items": preview, "total": len(preview)})