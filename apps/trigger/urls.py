from django.urls import path
from . import views

urlpatterns = [
    path("admin/triggers", views.TriggerListView.as_view()),
    path("admin/triggers/<uuid:trigger_id>", views.TriggerOperateView.as_view()),
    path("admin/triggers/<uuid:trigger_id>/toggle", views.TriggerToggleView.as_view()),
]