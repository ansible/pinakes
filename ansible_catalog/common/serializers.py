""" Serializers for Tags """
from rest_framework import serializers


class TagSerializer(serializers.Serializer):
    """serializer for tags"""

    name = serializers.CharField(max_length=100)


class TaskSerializer(serializers.Serializer):
    """Background task serializer."""

    id = serializers.CharField(max_length=64)
