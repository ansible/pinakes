""" Serializers for Approval Model."""
from rest_framework import serializers

from .basemodel import Tenant, Source
from .models import (
    ServiceInventory,
    ServiceOffering,
    ServiceOfferingNode,
    ServicePlan
)


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant"""

    class Meta:
        model = Tenant
        fields = (
            "id",
            "external_tenant",
        )


class SourceSerializer(serializers.ModelSerializer):
    """Serializer for Source"""

    class Meta:
        model = Source
        fields = (
            "id",
            "name"
        )

class ServiceInventorySerializer(serializers.ModelSerializer):
    """Serializer for ServiceInventory."""

    class Meta:
        model = ServiceInventory
        fields = ("id",
                  "description",
                  "extra",
                  "source_ref",
                  "source_created_at",
                  "source_updated_at",
                  "created_at",
                  "updated_at"
                 )
        ordering = ["-created_at"]
        read_only_fields = ("created_at", "updated_at")

class ServiceOfferingSerializer(serializers.ModelSerializer):
    """Serializer for ServiceOffering."""

    class Meta:
        model = ServiceOffering
        fields = ("id",
                  "name",
                  "description",
                  "survey_enabled",
                  "kind",
                  "extra",
                  "service_inventory"
                 )
        ordering = ["-created_at"]
        read_only_fields = ("created_at", "updated_at")

class ServiceOfferingNodeSerializer(serializers.ModelSerializer):
    """Serializer for ServiceOfferingNode."""

    class Meta:
        model = ServiceOfferingNode
        fields = ("id",
                  "service_inventory",
                  "service_offering",
                  "root_service_offering",
                  "extra"
                 )
        ordering = ["-created_at"]
        read_only_fields = ("created_at", "updated_at")

class ServicePlanSerializer(serializers.ModelSerializer):
    """Serializer for ServicePlan."""

    class Meta:
        model = ServicePlan
        fields = ("id",
                  "name",
                  "extra",
                  "create_json_schema",
                  "update_json_schema",
                  "service_offering"
                 )
        ordering = ["-created_at"]
        read_only_fields = ("created_at", "updated_at")
