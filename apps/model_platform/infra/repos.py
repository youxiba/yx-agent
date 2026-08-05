from model_platform.models import Model


class ModelRepository:
    def get(self,model_id: str)->Model:
        return Model.objects.get(id=model_id)

    def query(self, *, workspace_id = None, provider=None):
        qs = Model.objects.all().order_by('-create_time')
        if workspace_id: qs = qs.filter(workspace_id=workspace_id)
        if provider: qs = qs.filter(provider=provider)
        return qs

    