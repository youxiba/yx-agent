from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken,TokenError

from .serializers import LoginSerializer,RefreshSerializer,LogoutSerializer
from common.auth.tokens import issue_token_pair
from common.result import Result


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        return Result.success(issue_token_pair(ser.validated_data["user"]))

class RefreshView(APIView):
    authentication_classes = []

    def post(self, request):
        ser = RefreshSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            refresh = RefreshToken(ser.validated_data["refresh"])
            return Result.success({"access":str(refresh.access_token)})
        except TokenError:
            return Result.error("refresh token 无效", code=401)

class LogoutView(APIView):
    def post(self, request):
        ser = LogoutSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            RefreshToken(ser.validated_data["refresh"]).blacklist()
        except TokenError:
            pass
        return Result.success()