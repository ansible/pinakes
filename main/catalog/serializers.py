""" Serializers for Catalog Model."""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

from main.models import Tenant, Image
from main.catalog.models import (
    ApprovalRequest,
    CatalogServicePlan,
    Order,
    OrderItem,
    Portfolio,
    PortfolioItem,
    ProgressMessage,
)


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant"""

    class Meta:
        model = Tenant
        fields = (
            "id",
            "external_tenant",
        )


class PortfolioSerializer(serializers.ModelSerializer):
    """Serializer for Portfolio, which is a wrapper for PortfolioItems."""

    icon_url = serializers.SerializerMethodField("get_icon_url")

    class Meta:
        model = Portfolio
        fields = (
            "id",
            "name",
            "description",
            "icon_url",
            "created_at",
            "updated_at",
        )
        ordering = ["-created_at"]
        read_only_fields = ("created_at", "updated_at")

    def create(self, validated_data):
        return Portfolio.objects.create(
            tenant=Tenant.current(), **validated_data
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_icon_url(self, obj):
        request = self.context.get("request")
        return (
            request.build_absolute_uri(obj.icon.file.url)
            if obj.icon is not None
            else None
        )


class PortfolioItemSerializer(serializers.ModelSerializer):
    """Serializer for PortfolioItem, which maps to a Tower Job Template
    via the service_offering_ref."""

    icon_url = serializers.SerializerMethodField("get_icon_url")

    class Meta:
        model = PortfolioItem
        fields = (
            "id",
            "name",
            "description",
            "service_offering_ref",
            "portfolio",
            "icon_url",
            "created_at",
            "updated_at",
        )

        read_only_fields = ("created_at", "updated_at")

    def create(self, validated_data):
        return PortfolioItem.objects.create(
            tenant=Tenant.current(), **validated_data
        )

    @extend_schema_field(OpenApiTypes.STR)
    def get_icon_url(self, obj):
        request = self.context.get("request")
        return (
            request.build_absolute_uri(obj.icon.file.url)
            if obj.icon is not None
            else None
        )


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order"""

    owner = serializers.ReadOnlyField()

    class Meta:
        model = Order
        fields = (
            "id",
            "state",
            "owner",
            "order_request_sent_at",
            "created_at",
            "updated_at",
            "completed_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def create(self, validated_data):
        user = self.context["request"].user
        return Order.objects.create(
            tenant=Tenant.current(), user=user, **validated_data
        )


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem"""

    owner = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "name",
            "count",
            "service_parameters",
            "provider_control_parameters",
            "state",
            "portfolio_item",
            "order",
            "external_url",
            "artifacts",
            "owner",
            "order_request_sent_at",
            "created_at",
            "updated_at",
            "completed_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def create(self, validated_data):
        user = self.context["request"].user
        return OrderItem.objects.create(
            tenant=Tenant.current(), user=user, **validated_data
        )


class ImageSerializer(serializers.ModelSerializer):
    """Serializer for Image"""

    file = serializers.ImageField(
        required=False, max_length=None, use_url=True
    )

    class Meta:
        model = Image
        fields = (
            "id",
            "source_ref",
            "file",
        )


class ApprovalRequestSerializer(serializers.ModelSerializer):
    """Serializer for ApprovalRequest"""

    class Meta:
        model = ApprovalRequest
        fields = (
            "id",
            "approval_request_ref",
            "order",
            "reason",
            "request_completed_at",
            "state",
        )


class ProgressMessageSerializer(serializers.ModelSerializer):
    """Serializer for ProgressMessage"""

    class Meta:
        model = ProgressMessage
        fields = (
            "received_at",
            "level",
            "message",
            "messageable_type",
            "messageable_id",
        )


class CatalogServicePlanSerializer(serializers.ModelSerializer):
    """Serializer for CatalogServicePlan"""

    class Meta:
        model = CatalogServicePlan
        fields = (
            "id",
            "name",
            "description",
            "create_json_schema",
            "imported",
            "modified",
            "portfolio_item",
            "created_at",
            "updated_at",
        )

    def create(self, validated_data):
        return CatalogServicePlan.objects.create(
            tenant=Tenant.current(), **validated_data
        )
