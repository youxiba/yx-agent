# coding=utf-8
from django.urls import path
from . import views

urlpatterns = [
    path("admin/knowledge/paragraph/split", views.ParagraphSplitView.as_view()),
]