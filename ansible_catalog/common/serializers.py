""" Serializers for Tags """
from rest_framework import serializers


class TagSerializer(serializers.Serializer):
    """Tag definition"""

    name = serializers.CharField(max_length=100, help_text="Tag name")


class TaskSerializer(serializers.Serializer):
    """Background task"""

    id = serializers.CharField(
        max_length=64,
        help_text="Task id that can be used to track the progress",
    )
