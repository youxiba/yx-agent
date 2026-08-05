import json

from rest_framework.views import APIView

from common.auth.decorators import require_permissions
from common.result import Result
from identity.permissions import P
from model_platform.infra.cipher import cipher
from model_platform.infra.repos import ModelRepository
from model_platform.models import Model, ModelType
from model_platform.registry import PROVIDERS
from model_platform.serializers import ModelSerializer
from model_platform.service.form import get_credential_form
from model_platform.service.gateway import gateway


class ProviderListView(APIView):
    @require_permissions(P.MODEL_READ)
    def get(self, request):
        return Result.success([p.get_provider_info() for p in PROVIDERS.values()])


class ProviderModelListView(APIView):
    @require_permissions(P.MODEL_READ)
    def get(self, request,provider):
        mt = request.query_params.get("model_type")
        if mt not in ModelType.values:
            return Result.error("model_type 无效",code = 400)
        infos = PROVIDERS[provider].get_model_list(ModelType[mt])
        return Result.success([{"name":i.name, "desc":i.desc} for i in infos])


class CredentialFormView(APIView):
    @require_permissions(P.MODEL_READ)
    def get(self, request,provider):
        return Result.success(get_credential_form(
            provider,request.query_params["model_type"],
            request.query_params["model_name"]
        ))

class ModelListView(APIView):
    @require_permissions(P.MODEL_READ)
    def get(self, request):
        qs = ModelRepository().query(workspace_id=request.query_params["workspace_id"])
        return Result.success([ModelSerializer(m).data for m in qs])

    @require_permissions(P.MODEL_WRITE)
    def post(self, request):
        data = request.data
        provider, model_type, model_name = data["provider"], data["model_type"], data["model_name"]
        if provider not in PROVIDERS:
            return Result.error("供应商不存在", code=400)
        if not PROVIDERS[provider].is_valid_credential(model_type, model_name, data["credential"]):
            return Result.error("凭据校验失败", code=400)
        row = Model.objects.create(
            name=data.get("name", model_name), provider=provider,
            model_type=model_type, model_name=model_name,
            credential=cipher.encrypt(json.dumps(data["credential"])),
            model_params=data.get("model_params", {}),
            is_cacheable=provider in ("ollama", "local"),
            user=request.user)
        return Result.success(ModelSerializer(row).data)


class ModelOperateView(APIView):
    @require_permissions(P.MODEL_WRITE)
    def put(self, request, model_id):
        row = Model.objects.filter(id=model_id).first()
        if not row:
            return Result.error("模型不存在", code=404)
        # 掩码字段用旧值填充：前端只传改动项
        if "credential" in request.data:
            old = json.loads(cipher.decrypt(row.credential))
            cred = {**old, **{k: v for k, v in request.data["credential"].items() if "****" not in str(v)}}
            row.credential = cipher.encrypt(json.dumps(cred))
        row.model_params = request.data.get("model_params", row.model_params)
        row.name = request.data.get("name", row.name)
        row.save()
        gateway.invalidate(str(row.id))
        return Result.success(ModelSerializer(row).data)

    @require_permissions(P.MODEL_WRITE)
    def delete(self, request, model_id):
        Model.objects.filter(id=model_id).delete()
        gateway.invalidate(model_id)
        return Result.success()


class ModelTestView(APIView):
    @require_permissions(P.MODEL_READ)
    def post(self, request, model_id):
        row = Model.objects.filter(id=model_id).first()
        if not row:
            return Result.error("模型不存在", code=404)
        ok = gateway.test(row)
        return Result.success({"ok": ok, "status": "SUCCESS" if ok else "ERROR"})