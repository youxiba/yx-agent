from django.urls import path
from . import views

urlpatterns = [
    path("admin/auth/login",views.LoginView.as_view()),
    path("admin/auth/refresh",views.RefreshView.as_view()),
    path("admin/auth/logout",views.LogoutView.as_view()),
]