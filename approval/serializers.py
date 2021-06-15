""" Serializers for Approval Model."""
from rest_framework import serializers

from .basemodel import Tenant
from .models import Template
from .models import Workflow


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant"""

    class Meta:
        model = Tenant
        fields = (
            "id",
            "external_tenant",
        )


class TemplateSerializer(serializers.ModelSerializer):
    """Serializer for Template."""

    class Meta:
        model = Template
        fields = ("id", "title", "description", "created_at", "updated_at")
        ordering = ["-created_at"]
        read_only_fields = ("created_at", "updated_at")

    def create(self, validated_data):
        tenant = Tenant.objects.all()[:1].get()
        return Template.objects.create(tenant=tenant, **validated_data)


class WorkflowSerializer(serializers.ModelSerializer):
    """Serializer for Workflow."""

    class Meta:
        model = Workflow
        ordering = ["-created_at"]
        fields = (
            "id",
            "name",
            "description",
            "template",
            "created_at",
            "updated_at",
        )

        read_only_fields = ("created_at", "updated_at")

    def create(self, validated_data):
        tenant = Tenant.objects.all()[:1].get()
        return Workflow.objects.create(tenant=tenant, **validated_data)
