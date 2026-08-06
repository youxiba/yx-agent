from django.urls import path
from . import views

urlpatterns = [
    path("chat/mcp", views.McpEndpointView.as_view()),
]
