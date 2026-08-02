from rest_framework import serializers

from common.verify import check_verify_code
from .models import User, Role
from .services import AuthService

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = AuthService.login(attrs['username'], attrs['password'])
        attrs['user'] = user
        return attrs

class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(min_length=3,max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8,write_only=True)
    code = serializers.CharField()

    def validate(self, attrs):
        if not check_verify_code(attrs['email'], attrs['code']):
            raise serializers.ValidationError({"验证码错误或已过期"})
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError({"用户名已存在"})
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("邮箱已注册")
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

class SendCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    new_password = serializers.CharField(min_length=8,write_only=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "phone", "nick_name", "role", "source", "is_active", "create_time", "update_time"]

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8,write_only=True)
    class Meta:
        model = User
        fields = ["username","email","phone","nick_name","role","password"]

    def create(self, validated_data):
        role = validated_data.pop("role",Role.USER)
        return User.objects.create_user(**validated_data,role=role)

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email","phone","nick_name","role","is_active"]


