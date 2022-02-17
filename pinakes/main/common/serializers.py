from rest_framework import serializers

from pinakes.main.common import models


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Group
        fields = ("id", "name", "parent_id")
