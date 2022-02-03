from rest_framework import serializers

import jwt
from ansible_catalog.main.auth import models
from django.contrib.auth.models import User
from django.conf import settings
from drf_spectacular.utils import extend_schema_field, OpenApiTypes


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Group
        fields = ("id", "name", "parent_id")


class CurrentUserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField("get_roles")

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "roles")

    @extend_schema_field(
        {"type": "array", "items": {"type": OpenApiTypes.STR}}
    )
    def get_roles(self, obj):
        request = self.context.get("request")
        extra_data = request.keycloak_user.extra_data
        jot = jwt.decode(
            extra_data["access_token"], options={"verify_signature": False}
        )
        roles = (
            jot.get("resource_access", {})
            .get(settings.KEYCLOAK_CLIENT_ID, {})
            .get("roles", [])
        )
        return roles
