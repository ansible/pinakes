from rest_framework import serializers

from ansible_catalog.main.auth import models
from django.contrib.auth.models import User


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Group
        fields = ("id", "name", "parent_id")


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name")
