# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("admin/applications/<uuid:app_id>/workflow", views.ApplicationWorkflowView.as_view()),
    path("admin/applications/<uuid:app_id>/publish", views.ApplicationWorkflowView.as_view()),
    path("admin/applications/debug", views.ApplicationDebugView.as_view()),
]