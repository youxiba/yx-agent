import json

from rest_framework import serializers

from model_platform.infra.cipher import cipher
from model_platform.models import Model
from model_platform.service.form import mask_credential


class ModelSerializer(serializers.ModelSerializer):
    credential = serializers.SerializerMethodField()
    model_params = serializers.JSONField()

    class Meta:
        model = Model
        fields = ["id", "name", "provider", "model_type", "model_name", "credential",
                  "model_params", "is_cacheable", "status", "create_time"]

    def get_credential(self, obj):
        cred = json.loads(cipher.decrypt(obj.credential))
        return mask_credential(cred)
