from django.urls import path, include

urlpatterns = [
    path('api/', include("common.urls")),
    path("api/",include("identity.urls")),
    path("api/",include("model_platform.urls")),
    path("api/", include("knowledge.urls")),
    path("api/", include("chat.urls")),
    path("api/", include("mcp.urls")),
    path("api/", include("trigger.urls")),


]