from rest_framework import serializers

from ansible_catalog.main.auth import models


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Group
        fields = ("id", "name", "parent_id")
