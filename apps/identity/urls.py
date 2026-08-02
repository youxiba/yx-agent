from django.urls import path
from . import views

urlpatterns = [
    path("public/send_code",views.SendCodeView.as_view()),
    path("public/reset_password",views.ResetPasswordView.as_view()),
    path("public/register",views.RegisterView.as_view()),
    path("admin/auth/login", views.LoginView.as_view()),
    path("admin/auth/refresh", views.RefreshView.as_view()),
    path("admin/auth/logout", views.LogoutView.as_view()),
    path("admin/users",views.UserListView.as_view()),
    path("admin/user/batch_delete",views.UserBatchDeleteView.as_view()),
    path("admin/user/<uuid:user_id>",views.UserOperateView.as_view()),
]