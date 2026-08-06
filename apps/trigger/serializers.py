from rest_framework import serializers
from .models import Trigger, TriggerTask


class TriggerTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriggerTask
        fields = ["id", "source_type", "target_id", "task_args", "is_active"]


class TriggerSerializer(serializers.ModelSerializer):
    tasks = TriggerTaskSerializer(many=True, required=False)

    class Meta:
        model = Trigger
        fields = ["id", "name", "trigger_type", "setting", "is_active", "tasks", "create_time", "update_time"]
        read_only_fields = ["id", "create_time", "update_time"]

    def create(self, validated_data):
        task_list = validated_data.pop("tasks", [])
        t = Trigger.objects.create(**validated_data)
        for tk in task_list:
            TriggerTask.objects.create(trigger=t, **tk)
        return t

    def update(self, instance, validated_data):
        task_list = validated_data.pop("tasks", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if task_list is not None:                       # 整体替换策略：子任务先删后建
            instance.tasks.all().delete()
            for tk in task_list:
                TriggerTask.objects.create(trigger=instance, **tk)
        return instance