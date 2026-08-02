# apps/common/views.py
from django.http import JsonResponse

def health(request):
    return JsonResponse({"code": 0,"message":"ok", "data":{"status": "UP"}})

