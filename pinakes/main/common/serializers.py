from rest_framework import serializers

from pinakes.main.common import models


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Group
        fields = ("id", "name", "parent_id")


class AboutSerializer(serializers.Serializer):
    """Product and version info"""

    product_name = serializers.CharField(
        max_length=100,
        help_text="Name of the product",
    )
    version = serializers.CharField(
        max_length=32,
        help_text="Version of the product",
    )
