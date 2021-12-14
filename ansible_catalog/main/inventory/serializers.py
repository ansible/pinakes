""" Serializers for Inventory Model."""
from rest_framework import serializers

from ansible_catalog.main.models import Source
from ansible_catalog.main.inventory.models import (
    InventoryServicePlan,
    ServiceInstance,
    ServiceInventory,
    ServiceOffering,
    ServiceOfferingNode,
)


class SourceSerializer(serializers.ModelSerializer):
    """Serializer for Source"""

    class Meta:
        model = Source
        fields = ("id", "name")


class ServiceInventorySerializer(serializers.ModelSerializer):
    """Serializer for ServiceInventory."""

    class Meta:
        model = ServiceInventory
        fields = (
            "id",
            "description",
            "extra",
            "source_ref",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class ServiceOfferingSerializer(serializers.ModelSerializer):
    """Serializer for ServiceOffering."""

    class Meta:
        model = ServiceOffering
        fields = (
            "id",
            "name",
            "description",
            "survey_enabled",
            "kind",
            "extra",
            "service_inventory",
        )
        read_only_fields = ("created_at", "updated_at")


class ServiceOfferingNodeSerializer(serializers.ModelSerializer):
    """Serializer for ServiceOfferingNode."""

    class Meta:
        model = ServiceOfferingNode
        fields = (
            "id",
            "service_inventory",
            "service_offering",
            "root_service_offering",
            "extra",
        )
        read_only_fields = ("created_at", "updated_at")


class InventoryServicePlanSerializer(serializers.ModelSerializer):
    """Serializer for InventoryServicePlan."""

    class Meta:
        model = InventoryServicePlan
        fields = (
            "id",
            "name",
            "extra",
            "create_json_schema",
            "update_json_schema",
            "schema_sha256",
            "service_offering",
        )
        read_only_fields = ("created_at", "updated_at")


class ServiceInstanceSerializer(serializers.ModelSerializer):
    """Serializer for ServiceInstance."""

    class Meta:
        model = ServiceInstance
        fields = (
            "id",
            "name",
            "extra",
            "external_url",
            "service_offering",
            "service_plan",
        )
