from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework.views import APIView
from common.auth.decorators import require_permissions
from common.result import Result
from identity.permissions import P
from .models import Trigger, TaskRecord
from .serializers import TriggerSerializer
from .services import get_trigger


class TriggerListView(APIView):
    @require_permissions(P.TRIGGER_READ)
    def get(self, request):
        q = Q(workspace_id=request.workspace_id)
        if kw := request.query_params.get("keyword"):
            q &= Q(name__icontains=kw)
        page = int(request.query_params.get("page", 1))
        size = int(request.query_params.get("page_size", 10))
        pg = Paginator(Trigger.objects.filter(q).order_by("-create_time"), size)
        items = [TriggerSerializer(t).data for t in pg.page(page)]
        return Result.success({"items": items, "total": pg.count})

    @require_permissions(P.TRIGGER_WRITE)
    def post(self, request):
        ser = TriggerSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        t = ser.save(workspace_id=request.workspace_id, created_by=request.user)
        # 注：Day 2 接入调度后，这里补 register_trigger(t)
        return Result.success(TriggerSerializer(t).data)


class TriggerOperateView(APIView):
    @require_permissions(P.TRIGGER_READ)
    def get(self, request, trigger_id):
        return Result.success(TriggerSerializer(get_trigger(request, trigger_id)).data)

    @require_permissions(P.TRIGGER_WRITE)
    def put(self, request, trigger_id):
        t = get_trigger(request, trigger_id)
        ser = TriggerSerializer(t, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        # 注：Day 2 这里改为：启用定时则 register_trigger(t)，否则 unregister_trigger(t.id)
        return Result.success(TriggerSerializer(t).data)

    @require_permissions(P.TRIGGER_WRITE)
    def delete(self, request, trigger_id):
        t = get_trigger(request, trigger_id)
        # 注：Day 2 这里补 unregister_trigger(t.id)
        t.delete()
        return Result.success()


class TriggerToggleView(APIView):
    @require_permissions(P.TRIGGER_WRITE)
    def post(self, request, trigger_id):
        t = get_trigger(request, trigger_id)
        t.is_active = not t.is_active
        t.save(update_fields=["is_active", "update_time"])
        return Result.success({"is_active": t.is_active})