# views.py
import uuid
from django.db import transaction
from rest_framework.views import APIView
from chat.sse import EventEmitter
from common.result import Result
from common.exceptions import AppApiException
from common.auth.decorators import require_permissions
from identity.permissions import P
from application.models import Application, ApplicationVersion
from agent.engine.graph import WorkflowGraph, WorkflowGraphError
from agent.services import ApplicationWorkflowService


class ApplicationWorkflowView(APIView):
    @require_permissions(P.APPLICATION_WRITE)
    def get(self, request, app_id):
        app = Application.objects.filter(id=app_id).first()
        if not app:
            return Result.error("应用不存在", code=404)
        return Result.success({"id": str(app.id), "name": app.name, "work_flow": app.work_flow})

    @require_permissions(P.APPLICATION_WRITE)
    def put(self, request, app_id):
        app = Application.objects.filter(id=app_id).first()
        if not app:
            return Result.error("应用不存在", code=404)
        wf = request.data.get("work_flow")
        try:
            WorkflowGraph.from_json(wf).validate()      # 保存前必过图校验
        except WorkflowGraphError as e:
            return Result.error(f"工作流图非法: {e}", code=400)
        app.work_flow = wf
        app.name = request.data.get("name", app.name)
        app.save(update_fields=["work_flow", "name", "update_time"])
        return Result.success({"id": str(app.id)})

    @require_permissions(P.APPLICATION_WRITE)
    def post(self, request, app_id):
        """发布：冻结快照到 ApplicationVersion（运行时读已发布版本）。"""
        app = Application.objects.filter(id=app_id).first()
        if not app:
            return Result.error("应用不存在", code=404)
        WorkflowGraph.from_json(app.work_flow).validate()
        with transaction.atomic():
            ApplicationVersion.objects.filter(application=app, is_published=True) \
                .update(is_published=False)
            ApplicationVersion.objects.create(application=app,
                                              work_flow_snapshot=app.work_flow,
                                              is_published=True)
        return Result.success({"published": True})


class ApplicationDebugView(APIView):
    """调试通道：阻塞等流结束，返回拼接文本（生产运行走异步 chat 通道）。"""
    @require_permissions(P.APPLICATION_READ)
    def post(self, request):
        wf = request.data.get("work_flow")
        try:
            graph = WorkflowGraph.from_json(wf); graph.validate()
        except WorkflowGraphError as e:
            return Result.error(f"工作流图非法: {e}", code=400)
        # 单测/开发注入 services；生产用真实 gateway/vector_store 装配
        services = _build_services(request)
        svc = ApplicationWorkflowService(services)
        em = EventEmitter()
        # 简化：调 svc.execute 并收集 SSE 文本（生产走流式 HttpResponse）
        import json
        store = svc.execute(Application(work_flow=wf, name="debug"),
                            {"question": request.data.get("question", "")}, em)
        return Result.success({"answer": store.global_vars.get("answer", "")})


def _build_services(request) -> dict:
    """装配 gateway/vector_store/splitter 等注入服务（沿用 Phase2/3 单例）。"""
    from model_platform.service.gateway import ModelGateway
    gateway = ModelGateway.instance()
    return {"gateway": gateway}