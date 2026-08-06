# coding=utf-8
"""工具序列化器：input_schema 必须是合法 JSON Schema"""
import jsonschema
from rest_framework import serializers
from .models import Tool, ToolRecord


class ToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = ["id", "name", "label", "desc", "code", "input_schema", "is_builtin",
                  "status", "create_time", "update_time"]
        read_only_fields = ["id", "is_builtin", "status", "create_time", "update_time"]

    def validate_input_schema(self, value):
        if not isinstance(value, dict) or value.get("type") != "object":
            raise serializers.ValidationError("input_schema 必须是 type=object 的 JSON Schema")
        try:
            jsonschema.Draft7Validator.check_schema(value)
        except jsonschema.SchemaError as e:
            raise serializers.ValidationError(f"input_schema 非法: {e}")
        return value


class ToolRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolRecord
        fields = ["id", "tool_id", "chat_id", "inputs", "output", "status",
                  "run_time_ms", "created_at"]
        read_only_fields = fields