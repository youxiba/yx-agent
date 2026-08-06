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
    path("admin/knowledge/<uuid:knowledge_id>/document", views.DocumentListView.as_view()),
    path("admin/knowledge/document/batch", views.DocumentBatchView.as_view()),
    path("admin/knowledge/document/<uuid:document_id>", views.DocumentOperateView.as_view()),
    path("admin/knowledge/document/<uuid:document_id>/refresh", views.DocumentRefreshView.as_view()),
    # TODO(Phase3 Day5): 段落/问题管理视图未建，先注释；建好 ParagraphListView/Batch/Operate、ProblemListView/Operate 后打开
    # path("admin/knowledge/document/<uuid:document_id>/paragraph", views.ParagraphListView.as_view()),
    # path("admin/knowledge/paragraph/batch", views.ParagraphBatchView.as_view()),
    # path("admin/knowledge/paragraph/<uuid:paragraph_id>", views.ParagraphOperateView.as_view()),
    # path("admin/knowledge/paragraph/<uuid:paragraph_id>/problem", views.ProblemListView.as_view()),
    # path("admin/knowledge/problem/<uuid:problem_id>", views.ProblemOperateView.as_view()),
    path("admin/termbase", views.TermbaseListView.as_view()),
    path("admin/termbase/<uuid:termbase_id>", views.TermbaseOperateView.as_view()),
    path("admin/termbase/<uuid:termbase_id>/term", views.TermListView.as_view()),
    path("admin/termbase/term/<uuid:term_id>", views.TermOperateView.as_view()),
]