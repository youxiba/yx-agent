# coding=utf-8
import io
import json
import os
import zipfile
from urllib.parse import quote

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from rest_framework.views import APIView
from common.result import Result
from identity.permissions import P
from common.auth.decorators import require_permissions
from identity.services import WorkspaceService
from .infra import index_service
from .infra.vector_store import PGVectorStore
from .models import Knowledge, KnowledgeFolder, VectorType, Document, Problem, Paragraph, Term, Termbase, DocumentType
from .serializers import DocumentSerializer, FolderSerializer, KnowledgeSerializer, ProblemSerializer, TermSerializer, \
    TermbaseSerializer, ParagraphSerializer
from .services.ingest import DocumentIngestService
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

class DocumentListView(APIView):
    """GET 文档列表 / POST 上传文档（multipart: file, type, folder_id, meta, limit）"""
    @require_permissions(P.KNOWLEDGE_READ)
    def get(self, request, knowledge_id):
        k = get_knowledge(request, knowledge_id)
        q = Q(knowledge=k, is_active=True)
        if kw := request.query_params.get("name"):
            q &= Q(name__icontains=kw)
        page = int(request.query_params.get("page", 1))
        size = int(request.query_params.get("page_size", 10))
        qs = k.documents.filter(q).order_by("-update_time")
        pg = Paginator(qs, size)
        return Result.success({"items": [DocumentSerializer(d).data for d in pg.page(page)], "total": pg.count})

    @require_permissions(P.KNOWLEDGE_WRITE)
    def post(self, request, knowledge_id):
        k = get_knowledge(request, knowledge_id)
        upload = request.FILES.get("file")
        if upload is None:
            return Result.error("缺少上传文件", code=400)
        doc_type = request.data.get("type", "base")
        meta = json.loads(request.data.get("meta", "{}") or "{}")
        meta.setdefault("limit", int(request.data.get("limit", 256)))
        doc = DocumentIngestService().upload(k, request.user, upload, doc_type, meta)
        return Result.success(DocumentSerializer(doc).data)


class DocumentOperateView(APIView):
    """PUT/DELETE /api/admin/knowledge/document/{id}"""
    @require_permissions(P.KNOWLEDGE_WRITE)
    def put(self, request, document_id):
        doc = Document.objects.filter(id=document_id).first()
        if not doc:
            return Result.error("文档不存在", code=404)
        get_knowledge(request, str(doc.knowledge_id))
        ser = DocumentSerializer(doc, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Result.success(DocumentSerializer(doc).data)

    @require_permissions(P.KNOWLEDGE_WRITE)
    def delete(self, request, document_id):
        doc = Document.objects.filter(id=document_id).first()
        if not doc:
            return Result.error("文档不存在", code=404)
        get_knowledge(request, str(doc.knowledge_id))
        from .infra.vector_store import PGVectorStore
        PGVectorStore().delete_by_document_ids([str(doc.id)])
        doc.delete()    # 级联段落/问题/Embedding
        return Result.success()


class DocumentBatchView(APIView):
    """POST /api/admin/knowledge/document/batch  {ids, operation: delete|move, folder_id}"""
    @require_permissions(P.KNOWLEDGE_WRITE)
    def post(self, request):
        ids = request.data.get("ids", [])
        operation = request.data.get("operation", "delete")
        if operation == "move":
            Document.objects.filter(id__in=ids).update(folder_id=request.data.get("folder_id"))
        else:
            PGVectorStore().delete_by_document_ids(ids)
            Document.objects.filter(id__in=ids).delete()
        return Result.success()


class DocumentRefreshView(APIView):
    """POST /api/admin/knowledge/document/{id}/refresh  重新向量化单文档"""
    @require_permissions(P.KNOWLEDGE_WRITE)
    def post(self, request, document_id):
        doc = Document.objects.filter(id=document_id).first()
        if not doc:
            return Result.error("文档不存在", code=404)
        get_knowledge(request, str(doc.knowledge_id))
        from .services.ingest import DocumentIngestService
        DocumentIngestService().refresh_document(str(doc.id))
        return Result.success({"message": "刷新已排队"})

    class ParagraphListView(APIView):
        """GET /api/admin/knowledge/document/{id}/paragraph  段落列表（分页）"""

        @require_permissions(P.KNOWLEDGE_READ)
        def get(self, request, document_id):
            doc = Document.objects.filter(id=document_id).first()
            if not doc:
                return Result.error("文档不存在", code=404)
            get_knowledge(request, str(doc.knowledge_id))
            q = Q(document=doc, is_active=True)
            if kw := request.query_params.get("content"):
                q &= Q(content__icontains=kw)
            page = int(request.query_params.get("page", 1))
            size = int(request.query_params.get("page_size", 20))
            qs = doc.paragraphs.filter(q).order_by("create_time")
            pg = Paginator(qs, size)
            items = []
            for p in pg.page(page):
                data = ParagraphSerializer(p).data
                data["problems"] = [ProblemSerializer(pp).data for pp in p.problems.filter(is_active=True)]
                items.append(data)
            return Result.success({"items": items, "total": pg.count})

    class ParagraphOperateView(APIView):
        """PUT/DELETE /api/admin/knowledge/paragraph/{id}"""

        @require_permissions(P.KNOWLEDGE_WRITE)
        def put(self, request, paragraph_id):
            p = Paragraph.objects.filter(id=paragraph_id).first()
            if not p:
                return Result.error("段落不存在", code=404)
            get_knowledge(request, str(p.knowledge_id))
            ser = ParagraphSerializer(p, data=request.data, partial=True)
            ser.is_valid(raise_exception=True)
            old_hash = p.compare_content_hash
            ser.save()
            if p.compare_content_hash != old_hash:
                from .services.ingest import DocumentIngestService
                DocumentIngestService().refresh_document(str(p.document_id))  # 内容变更触发重向量化
            return Result.success(ParagraphSerializer(p).data)

        @require_permissions(P.KNOWLEDGE_WRITE)
        def delete(self, request, paragraph_id):
            p = Paragraph.objects.filter(id=paragraph_id).first()
            if not p:
                return Result.error("段落不存在", code=404)
            get_knowledge(request, str(p.knowledge_id))
            from .infra.vector_store import PGVectorStore
            PGVectorStore().delete_by_paragraph_ids([str(p.id)])
            p.delete()
            return Result.success()

    class ParagraphBatchView(APIView):
        """POST /api/admin/knowledge/paragraph/batch  {ids, operation: delete|move, document_id}"""

        @require_permissions(P.KNOWLEDGE_WRITE)
        def post(self, request):
            ids = request.data.get("ids", [])
            operation = request.data.get("operation", "delete")
            if operation == "move":
                Paragraph.objects.filter(id__in=ids).update(document_id=request.data.get("document_id"))
            else:
                PGVectorStore().delete_by_paragraph_ids(ids)
                Paragraph.objects.filter(id__in=ids).delete()
            return Result.success()

    class ProblemListView(APIView):
        """GET/POST /api/admin/knowledge/paragraph/{id}/problem  问题列表与新增"""

        @require_permissions(P.KNOWLEDGE_READ)
        def get(self, request, paragraph_id):
            p = Paragraph.objects.filter(id=paragraph_id).first()
            if not p:
                return Result.error("段落不存在", code=404)
            get_knowledge(request, str(p.knowledge_id))
            return Result.success([ProblemSerializer(pp).data for pp in p.problems.filter(is_active=True)])

        @require_permissions(P.KNOWLEDGE_WRITE)
        def post(self, request, paragraph_id):
            p = Paragraph.objects.filter(id=paragraph_id).first()
            if not p:
                return Result.error("段落不存在", code=404)
            get_knowledge(request, str(p.knowledge_id))
            content = request.data.get("content")
            if not content:
                return Result.error("content 必填", code=400)
            pp = Problem.objects.create(paragraph=p, content=content)
            return Result.success(ProblemSerializer(pp).data)

    class ProblemOperateView(APIView):
        """PUT/DELETE /api/admin/knowledge/problem/{id}"""

        @require_permissions(P.KNOWLEDGE_WRITE)
        def put(self, request, problem_id):
            pp = Problem.objects.filter(id=problem_id).first()
            if not pp:
                return Result.error("问题不存在", code=404)
            get_knowledge(request, str(pp.paragraph.knowledge_id))
            pp.content = request.data.get("content", pp.content)
            pp.save(update_fields=["content"])
            return Result.success(ProblemSerializer(pp).data)

        @require_permissions(P.KNOWLEDGE_WRITE)
        def delete(self, request, problem_id):
            Problem.objects.filter(id=problem_id).delete()
            return Result.success()

class TermbaseListView(APIView):
    """GET/POST /api/admin/termbase"""
    @require_permissions(P.KNOWLEDGE_READ)
    def get(self, request):
        q = Q(workspace_id__in=request.user.memberships.values_list("workspace_id", flat=True))
        if kw := request.query_params.get("keyword"):
            q &= Q(name__icontains=kw)
        qs = Termbase.objects.filter(q).order_by("-update_time")
        return Result.success({"items": [TermbaseSerializer(t).data for t in qs], "total": qs.count()})

    @require_permissions(P.KNOWLEDGE_WRITE)
    def post(self, request):
        from identity.models import Workspace
        ws = Workspace.objects.filter(id=request.data.get("workspace_id")).first()
        if ws is None:
            return Result.error("工作空间不存在", code=400)
        WorkspaceService.ensure_member(ws, request.user)
        tb = Termbase.objects.create(name=request.data.get("name"), workspace=ws, user=request.user)
        return Result.success(TermbaseSerializer(tb).data)


class TermbaseOperateView(APIView):
    """PUT/DELETE /api/admin/termbase/{id}"""
    @require_permissions(P.KNOWLEDGE_WRITE)
    def put(self, request, termbase_id):
        tb = Termbase.objects.filter(id=termbase_id).first()
        if not tb:
            return Result.error("术语库不存在", code=404)
        WorkspaceService.ensure_member(tb.workspace, request.user)
        tb.name = request.data.get("name", tb.name)
        tb.save(update_fields=["name"])
        return Result.success(TermbaseSerializer(tb).data)

    @require_permissions(P.KNOWLEDGE_WRITE)
    def delete(self, request, termbase_id):
        Termbase.objects.filter(id=termbase_id).delete()
        return Result.success()


class TermListView(APIView):
    """GET/POST /api/admin/termbase/{id}/term"""
    @require_permissions(P.KNOWLEDGE_READ)
    def get(self, request, termbase_id):
        tb = Termbase.objects.filter(id=termbase_id).first()
        if not tb:
            return Result.error("术语库不存在", code=404)
        WorkspaceService.ensure_member(tb.workspace, request.user)
        terms = tb.terms.filter(is_active=True).order_by("create_time")
        return Result.success({"items": [TermSerializer(t).data for t in terms], "total": terms.count()})

    @require_permissions(P.KNOWLEDGE_WRITE)
    def post(self, request, termbase_id):
        tb = Termbase.objects.filter(id=termbase_id).first()
        if not tb:
            return Result.error("术语库不存在", code=404)
        WorkspaceService.ensure_member(tb.workspace, request.user)
        t = Term.objects.create(termbase=tb, content=request.data.get("content"))
        return Result.success(TermSerializer(t).data)


class TermOperateView(APIView):
    """PUT/DELETE /api/admin/termbase/term/{id}"""
    @require_permissions(P.KNOWLEDGE_WRITE)
    def put(self, request, term_id):
        t = Term.objects.filter(id=term_id).first()
        if not t:
            return Result.error("术语不存在", code=404)
        t.content = request.data.get("content", t.content)
        t.save(update_fields=["content"])
        return Result.success(TermSerializer(t).data)

    @require_permissions(P.KNOWLEDGE_WRITE)
    def delete(self, request, term_id):
        Term.objects.filter(id=term_id).delete()
        return Result.success()

class KnowledgeExportView(APIView):
    """GET /api/admin/knowledge/{id}/export  导出 zip（源码文件 + 无文件的转 md）"""
    @require_permissions(P.KNOWLEDGE_READ)
    def get(self, request, knowledge_id):
        k = get_knowledge(request, knowledge_id)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for doc in k.documents.filter(is_active=True, type=DocumentType.BASE):
                path = doc.meta.get("file_path")
                if path and os.path.exists(path):
                    zf.write(path, arcname=f"{k.name}/{doc.name}")
                else:
                    md = self._doc_to_md(doc)
                    if md:
                        zf.writestr(f"{k.name}/{doc.name}.md", md)
        resp = HttpResponse(buf.getvalue(), content_type="application/zip")
        resp["Content-Disposition"] = f'attachment; filename="{quote(k.name)}.zip"'
        return resp

    @staticmethod
    def _doc_to_md(doc) -> str:
        lines = [f"# {doc.name}", ""]
        for p in doc.paragraphs.filter(is_active=True):
            lines.append(f"## {p.title}" if p.title else "## ")
            lines.append(p.content)
            for pp in p.problems.filter(is_active=True):
                lines.append(f"- 关联问题：{pp.content}")
            lines.append("")
        return "\n".join(lines)


class TemplateDownloadView(APIView):
    """GET /api/admin/knowledge/template?type=qa|table  导入模板下载"""
    @require_permissions(P.KNOWLEDGE_WRITE)
    def get(self, request):
        tpl = request.query_params.get("type", "qa")
        if tpl == "table":
            wb = Workbook()
            ws = wb.active
            ws.title = "sheet1"
            ws.append(["姓名", "部门", "职位"])
            ws.append(["张三", "研发", "工程师"])
            buf = io.BytesIO()
            wb.save(buf)
            resp = HttpResponse(buf.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            resp["Content-Disposition"] = 'attachment; filename="table_template.xlsx"'
            return resp
        content = (
            "问题1：MaxKB 支持哪些部署方式？\n"
            "回答1：支持 Docker Compose 一键部署与 K8s Helm 部署。\n\n"
            "问题2：如何配置本地向量模型？\n"
            "回答2：在模型平台选择 local 供应商并下载模型即可。\n"
        )
        resp = HttpResponse(content, content_type="text/plain; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="qa_template.md"'
        return resp

class DocumentSyncView(APIView):
    """POST /api/admin/knowledge/document/{id}/sync  手动同步 Web 文档"""

    @require_permissions(P.KNOWLEDGE_WRITE)
    def post(self, request, document_id):
        doc = Document.objects.filter(id=document_id, type=DocumentType.WEB).first()
        if not doc:
            return Result.error("Web 文档不存在", code=404)
        get_knowledge(request, str(doc.knowledge_id))
        from .tasks import sync_web_document
        sync_web_document.delay(str(doc.id))
        return Result.success({"message": "同步已排队"})