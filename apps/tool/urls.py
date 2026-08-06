from django.urls import path, include
from . import views

urlpatterns = [
    path("admin/tools", views.ToolListView.as_view()),
    path("admin/tools/<uuid:tool_id>", views.ToolOperateView.as_view()),
    path("api/", include("tool.urls")),
    path("admin/tools/<uuid:tool_id>/publish", views.ToolPublishView.as_view()),
    path("admin/tools/<uuid:tool_id>/export", views.ToolExportView.as_view()),
    path("admin/tools/import", views.ToolImportView.as_view()),
]