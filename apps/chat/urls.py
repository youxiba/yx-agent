# apps/chat/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("chat/<uuid:app_id>/chat", views.ChatView.as_view()),
]