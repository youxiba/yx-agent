# coding=utf-8
from django.core.paginator import Paginator
from rest_framework.views import APIView
from common.result import Result
from identity.permissions import P
from common.auth.decorators import require_permissions
from identity.services import WorkspaceService
from .infra import index_service
from .infra.vector_store import PGVectorStore
from .models import Knowledge, KnowledgeFolder, VectorType
from .services.knowledge import get_knowledge
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

class HitTestView(APIView):
    """POST /api/admin/knowledge/{id}/hit_test  body: {query, mode, top_n, similarity}"""
    @require_permissions(P.KNOWLEDGE_READ)
    def post(self, request, knowledge_id):
        k = get_knowledge(request, knowledge_id)
        query = request.data.get("query")
        if not query:
            return Result.error("query 必填", code=400)
        mode = request.data.get("mode", "embedding")
        top_n = int(request.data.get("top_n", 3))
        similarity = float(request.data.get("similarity", 0.5))
        from knowledge.services.retrieval import RetrievalService
        hits = RetrievalService().hit_test(k, query, mode, top_n, similarity)
        return Result.success({"hits": hits, "mode": mode, "total": len(hits)})

class KnowledgeListView(APIView):
    """GET/POST /api/admin/knowledge  列表（分页+名称搜索）与创建"""
    @require_permissions(P.KNOWLEDGE_READ)
    def get(self, request):
        q = Q(workspace_id=request.user.memberships.values_list("workspace_id", flat=True)[:1] or None)
        if kw := request.query_params.get("keyword"):
            q &= Q(name__icontains=kw)
        page = int(request.query_params.get("page", 1))
        size = int(request.query_params.get("page_size", 10))
        qs = Knowledge.objects.filter(q).order_by("-update_time")
        pg = Paginator(qs, size)
        return Result.success({"items": [KnowledgeSerializer(k).data for k in pg.page(page)], "total": pg.count})

    @require_permissions(P.KNOWLEDGE_WRITE)
    def post(self, request):
        from identity.models import Workspace
        ws_id = request.data.get("workspace_id")
        ws = Workspace.objects.filter(id=ws_id).first()
        if ws is None:
            return Result.error("工作空间不存在", code=400)
        WorkspaceService.ensure_member(ws, request.user)
        ser = KnowledgeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        k = ser.save(user=request.user, workspace=ws)
        if k.vector_type == VectorType.VECTOR and k.embedding_model_id:
            dim = self._get_dim(k.embedding_model_id)
            index_service.create_index(str(k.id), dim)
        return Result.success(KnowledgeSerializer(k).data)

    @staticmethod
    def _get_dim(model_id: str) -> int:
        from model_platform.service.gateway import gateway
        return gateway.get_model(model_id).get_vector_dim()


class KnowledgeOperateView(APIView):
    """PUT/DELETE /api/admin/knowledge/{id}"""
    @require_permissions(P.KNOWLEDGE_WRITE)
    def put(self, request, knowledge_id):
        k = get_knowledge(request, knowledge_id)
        ser = KnowledgeSerializer(k, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        if k.vector_type != VectorType.VECTOR:
            index_service.drop_index(str(k.id))
        return Result.success(KnowledgeSerializer(k).data)

    @require_permissions(P.KNOWLEDGE_WRITE)
    def delete(self, request, knowledge_id):
        k = get_knowledge(request, knowledge_id)
        index_service.drop_index(str(k.id))
        from .infra.vector_store import PGVectorStore
        PGVectorStore().delete_by_knowledge_ids([str(k.id)])
        k.delete()
        return Result.success()


class KnowledgeBatchView(APIView):
    """POST /api/admin/knowledge/batch  {ids: [...], operation: delete|move, folder_id}"""
    @require_permissions(P.KNOWLEDGE_WRITE)
    def post(self, request):
        ids = request.data.get("ids", [])
        operation = request.data.get("operation", "delete")
        if operation == "move":
            Knowledge.objects.filter(id__in=ids).update(folder_id=request.data.get("folder_id"))
        else:
            for kid in ids:
                k = Knowledge.objects.filter(id=kid).first()
                if k:
                    index_service.drop_index(str(k.id))
            PGVectorStore().delete_by_knowledge_ids(ids)
            Knowledge.objects.filter(id__in=ids).delete()
        return Result.success()


class KnowledgeFolderView(APIView):
    """GET 文件夹树 / POST 创建文件夹"""
    @require_permissions(P.KNOWLEDGE_READ)
    def get(self, request, knowledge_id=None):
        folders = KnowledgeFolder.objects.all()
        return Result.success(FolderSerializer(folders, many=True).data)

    @require_permissions(P.KNOWLEDGE_WRITE)
    def post(self, request):
        k = get_knowledge(request, request.data.get("knowledge_id"))
        parent_id = request.data.get("parent_id")
        folder = KnowledgeFolder.objects.create(knowledge=k, parent_id=parent_id, name=request.data.get("name", "未命名"))
        return Result.success(FolderSerializer(folder).data)


class KnowledgeRefreshView(APIView):
    """POST /api/admin/knowledge/{id}/refresh  整库重新向量化"""
    @require_permissions(P.KNOWLEDGE_WRITE)
    def post(self, request, knowledge_id):
        k = get_knowledge(request, knowledge_id)
        from .tasks import embed_by_knowledge
        embed_by_knowledge.delay(str(k.id))
        return Result.success({"message": "刷新已排队"})