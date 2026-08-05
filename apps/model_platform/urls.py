from django.urls import path
from . import views

urlpatterns = [
    path("admin/providers", views.ProviderListView.as_view()),
    path("admin/providers/<str:provider>/models", views.ProviderModelListView.as_view()),
    path("admin/providers/<str:provider>/credential_form", views.CredentialFormView.as_view()),
    path("admin/models", views.ModelListView.as_view()),
    path("admin/models/<uuid:model_id>", views.ModelOperateView.as_view()),
    path("admin/models/<uuid:model_id>/test", views.ModelTestView.as_view()),
]