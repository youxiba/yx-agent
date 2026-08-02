from django.urls import path, include

urlpatterns = [
    path('api/', include("common.urls")),
]