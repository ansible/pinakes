"""Serializer for auth object"""
from rest_framework import serializers

from jose import jwt

from django.conf import settings
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field


class CurrentUserSerializer(serializers.ModelSerializer):
    """Current user info to be sent to the caller"""

    roles = serializers.SerializerMethodField("get_roles")

    class Meta:
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "roles")

    @extend_schema_field(field={"type": "array", "items": {"type": "string"}})
    def get_roles(self, _obj):
        """Get the current users roles from the request"""
        request = self.context.get("request")
        jot = jwt.decode(
            request.auth,
            "",
            options={"verify_signature": False, "verify_aud": False},
        )
        roles = (
            jot.get("resource_access", {})
            .get(settings.KEYCLOAK_CLIENT_ID, {})
            .get("roles", [])
        )
        return roles
