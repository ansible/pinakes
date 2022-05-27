"""Serializers for Inventory Model."""
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop
from rest_framework import serializers

from pinakes.main.models import Source
from pinakes.main.inventory.models import (
    InventoryServicePlan,
    ServiceInstance,
    ServiceInventory,
    ServiceOffering,
    ServiceOfferingNode,
)


class SourceSerializer(serializers.ModelSerializer):
    """Serializer for Source"""

    refresh_state = serializers.SerializerMethodField()
    last_refresh_message = serializers.SerializerMethodField()
    availability_status = serializers.SerializerMethodField()
    availability_message = serializers.SerializerMethodField()

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
            "last_refresh_task_ref",
            "last_available_at",
            "last_checked_at",
            "availability_status",
            "availability_message",
            "info",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_refresh_state(self, obj):
        return _(obj.refresh_state)

    def get_last_refresh_message(self, obj):
        if obj.availability_status == "unavailable":
            return _("%(name)s is unavailable, refresh skipped") % {
                "name": obj.name
            }

        if obj.refresh_state == Source.State.FAILED:
            return _("Refresh failed: %(error)s") % {
                "error": obj.last_refresh_message
            }

        gettext_noop("adds")
        gettext_noop("deletes")
        gettext_noop("updates")
        sii_stats = obj.last_refresh_stats.get("service_inventory", {})
        soi_stats = obj.last_refresh_stats.get("service_offering", {})
        son_stats = obj.last_refresh_stats.get("service_offering_node", {})

        filtered_sii_stats = {
            _(key): value for key, value in sii_stats.items() if value > 0
        }
        filtered_soi_stats = {
            _(key): value for key, value in soi_stats.items() if value > 0
        }
        filtered_son_stats = {
            _(key): value for key, value in son_stats.items() if value > 0
        }

        obj.last_refresh_message = ""
        if bool(filtered_sii_stats):
            obj.last_refresh_message = _(
                "Service Inventories: %(stats)s;\n"
            ) % {"stats": filtered_sii_stats}

        if bool(filtered_soi_stats):
            obj.last_refresh_message += _(
                "Job Templates & Workflows: %(soi_stats)s;\n"
            ) % {"soi_stats": filtered_soi_stats}

        if bool(filtered_son_stats):
            obj.last_refresh_message += _(
                "Workflow Template Nodes: %(son_stats)s;\n"
            ) % {"son_stats": filtered_son_stats}

        if not obj.last_refresh_message:
            obj.last_refresh_message = _("Nothing to update")

        return _(obj.last_refresh_message)

    def get_availability_status(self, obj):
        return _(obj.availability_status)

    def get_availability_message(self, obj):
        if obj.availability_status == "unavailable":
            return self._create_localized_availability_message(obj)

        return _(obj.availability_message)

    def _create_localized_availability_message(self, obj):
        if obj.error_code == obj.__class__.ErrorCode.SOURCE_CANNOT_BE_CHANGED:
            params = {
                "new_url": obj.error_dict["new_url"],
                "new_install_uuid": obj.error_dict["new_install_uuid"],
                "url": obj.info["url"],
                "install_uuid": obj.info["install_uuid"],
            }
            return (
                _(
                    "Source cannot be changed to url %(new_url)s uuid \
%(new_install_uuid)s, currently bound to \
url %(url)s with uuid %(install_uuid)s"
                )
                % params
            )
        return _("Error: %(error)s") % {"error": obj.availability_message}


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
            "source",
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
