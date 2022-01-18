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
        fields = (
            "id",
            "name",
            "refresh_state",
            "refresh_started_at",
            "refresh_finished_at",
            "last_successful_refresh_at",
            "last_refresh_message",
            "last_available_at",
            "last_checked_at",
            "availability_status",
            "availability_message",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class ServiceInventorySerializer(serializers.ModelSerializer):
    """Serializer for ServiceInventory."""

    class Meta:
        model = ServiceInventory
        fields = (
            "id",
            "description",
            "name",
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
            "created_at",
            "updated_at",
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
        )
        read_only_fields = ("created_at", "updated_at")


class InventoryServicePlanSerializer(serializers.ModelSerializer):
    """Serializer for InventoryServicePlan."""

    class Meta:
        model = InventoryServicePlan
        fields = (
            "id",
            "name",
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
