# coding=utf-8
"""工具 CRUD API：列表（分页/关键字）/创建/详情/更新/删除"""
import _json

from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse
from rest_framework.views import APIView
from common.result import Result
from common.exceptions import AppApiException
from common.auth.decorators import require_permissions
from identity.permissions import P
from .infra.executor import ToolExecutor
from .infra.static_check import static_check
from .models import Tool
from .serializers import ToolSerializer
from .services import validate_inputs


class ToolListView(APIView):
    @require_permissions(P.TOOL_READ)
    def get(self, request):
        q = Q()
        if kw := request.query_params.get("keyword"):
            q &= Q(name__icontains=kw) | Q(label__icontains=kw)
        page = int(request.query_params.get("page", 1))
        size = int(request.query_params.get("page_size", 10))
        pg = Paginator(Tool.objects.filter(q).order_by("-create_time"), size)
        return Result.success({"items": [ToolSerializer(t).data for t in pg.page(page)], "total": pg.count})

    @require_permissions(P.TOOL_WRITE)
    def post(self, request):
        ser = ToolSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        tool = ser.save(creator=request.user)
        return Result.success(ToolSerializer(tool).data)


class ToolOperateView(APIView):
    def _get(self, request, tool_id) -> Tool:
        tool = Tool.objects.filter(id=tool_id).first()
        if not tool:
            raise AppApiException("工具不存在", code=404)
        return tool

    @require_permissions(P.TOOL_READ)
    def get(self, request, tool_id):
        return Result.success(ToolSerializer(self._get(request, tool_id)).data)

    @require_permissions(P.TOOL_WRITE)
    def put(self, request, tool_id):
        tool = self._get(request, tool_id)
        if tool.is_builtin:
            raise AppApiException("内置工具不可编辑", code=400)
        ser = ToolSerializer(tool, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Result.success(ToolSerializer(tool).data)

    @require_permissions(P.TOOL_WRITE)
    def delete(self, request, tool_id):
        self._get(request, tool_id).delete()
        return Result.success()

class ToolPublishView(APIView):
    @require_permissions(P.TOOL_WRITE)
    def post(self, request, tool_id):
        tool = ToolOperateView()._get(request, tool_id)   # 复用查找逻辑
        check = static_check(tool.code)
        if not check["ok"]:
            return Result.error(f"静态检查未通过: {check['messages'][:5]}", code=400)
        tool.status = Tool.Status.PUBLISHED
        tool.save(update_fields=["status", "update_time"])
        return Result.success(ToolSerializer(tool).data)


class ToolExportView(APIView):
    @require_permissions(P.TOOL_READ)
    def get(self, request, tool_id):
        tool = ToolOperateView()._get(request, tool_id)
        payload = {"name": tool.name, "label": tool.label, "desc": tool.desc,
                   "code": tool.code, "input_schema": tool.input_schema}
        return HttpResponse(
            _json.dumps(payload, ensure_ascii=False),
            content_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{tool.name}.tool.json"'})


class ToolImportView(APIView):
    @require_permissions(P.TOOL_WRITE)
    def post(self, request):
        data = request.data
        if isinstance(data, dict) and "content" in data:     # multipart 上传的 JSON 文件
            data = _json.loads(data["content"])
        for k in ("name", "code", "input_schema"):
            if k not in data:
                return Result.error(f"缺少字段 {k}", code=400)
        tool, _ = Tool.objects.update_or_create(
            name=data["name"],
            defaults={"label": data.get("label", data["name"]),
                      "desc": data.get("desc", ""), "code": data["code"],
                      "input_schema": data.get("input_schema", {"type": "object"})},
        )
        return Result.success(ToolSerializer(tool).data)

class ToolDebugView(APIView):
    """草稿态调试运行：静态检查 → schema 校验 → 沙箱执行，不落库（可选落 ToolRecord）"""

    @require_permissions(P.TOOL_WRITE)
    def post(self, request):
        code = request.data.get("code", "")
        inputs = request.data.get("inputs") or {}
        timeout = int(request.data.get("timeout", 30))
        tool_id = request.data.get("tool_id")
        check = static_check(code)
        if not check["ok"]:
            return Result.success({"status": "CHECK_FAIL", "ok": False, "check": check})
        schema = request.data.get("input_schema") or {"type": "object"}
        validate_inputs(schema, inputs)
        result = ToolExecutor().exec_code(code, inputs, timeout=timeout)
        if tool_id:                                       # 挂到真实工具上留审计
            from .models import Tool
            tool = Tool.objects.filter(id=tool_id).first()
            if tool:
                from .services import record_execution
                record_execution(tool, result, inputs=inputs, chat_id=request.data.get("chat_id"))
        return Result.success(result)