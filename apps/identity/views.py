from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken,TokenError

from common.verify import send_verify_code, check_verify_code
from .models import User
from .serializers import LoginSerializer, RefreshSerializer, LogoutSerializer, SendCodeSerializer, RegisterSerializer, \
    ResetPasswordSerializer
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

class SendCodeView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self,request):
        ser = SendCodeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        send_verify_code(ser.validated_data["email"])
        return Result.success()

class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self,request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Result.success(issue_token_pair(user))

class ResetPasswordView(APIView):
    authentication_classes = []
    permission_classes = []

    def psot(self,request):
        ser = ResetPasswordSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if not check_verify_code(ser.validated_data["email"], ser.validated_data["code"]):
            return Result.error("验证码错误或已过期", code=400)

        user = User.objects.filter(email=ser.validated_data["email"]).first()
        if not user:
            return Result.error("邮箱未注册", code=400)
        user.set_password(ser.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Result.success()