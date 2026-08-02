from rest_framework import serializers
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