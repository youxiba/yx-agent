from django.urls import path
from . import views

urlpatterns = [
    path("admin/knowledge/paragraph/split", views.ParagraphSplitView.as_view()),
    path("admin/knowledge", views.KnowledgeListView.as_view()),
    path("admin/knowledge/batch", views.KnowledgeBatchView.as_view()),
    path("admin/knowledge/folder", views.KnowledgeFolderView.as_view()),
    path("admin/knowledge/<uuid:knowledge_id>", views.KnowledgeOperateView.as_view()),
    path("admin/knowledge/<uuid:knowledge_id>/hit_test", views.HitTestView.as_view()),
    path("admin/knowledge/<uuid:knowledge_id>/refresh", views.KnowledgeRefreshView.as_view()),
]