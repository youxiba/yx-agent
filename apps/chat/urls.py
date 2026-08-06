# apps/chat/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("chat/<uuid:app_id>/chat", views.ChatView.as_view()),
    path("chat/<uuid:app_id>/chat/open", views.ChatOpenView.as_view()),
    path("chat/<uuid:app_id>/chat/list", views.ChatListView.as_view()),
    path("chat/<uuid:app_id>/chat/history", views.ChatHistoryView.as_view()),
    path("chat/<uuid:app_id>/chat/<uuid:chat_id>", views.ChatUpdateView.as_view()),
    path("chat/<uuid:app_id>/chat/<uuid:chat_id>/delete", views.ChatDeleteView.as_view()),
    path("chat/<uuid:app_id>/chat_record/<uuid:record_id>", views.ChatDetailView.as_view()),
    path("chat/<uuid:app_id>/chat_record/<uuid:record_id>/vote", views.ChatVoteView.as_view()),
    path("chat/<uuid:app_id>/chat_record/<uuid:record_id>/share", views.ChatShareView.as_view()),
]