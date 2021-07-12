""" Serializers for Catalog Model."""
from rest_framework import serializers

from .basemodel import Tenant
from .models import (
    Portfolio,
    PortfolioItem,
    Order,
    OrderItem
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

    class Meta:
        model = Portfolio
        fields = ("id", "name", "description", "created_at", "updated_at")
        ordering = ["-created_at"]
        read_only_fields = ("created_at", "updated_at")

    def create(self, validated_data):
        tenant = Tenant.objects.all()[:1].get()
        return Portfolio.objects.create(tenant=tenant, **validated_data)


class PortfolioItemSerializer(serializers.ModelSerializer):
    """Serializer for PortfolioItem, which maps to a Tower Job Template
    via the service_offering_ref."""

    class Meta:
        model = PortfolioItem
        ordering = ["-created_at"]
        fields = (
            "id",
            "name",
            "description",
            "service_offering_ref",
            "portfolio",
            "created_at",
            "updated_at",
        )

        read_only_fields = ("created_at", "updated_at")

    def create(self, validated_data):
        tenant = Tenant.objects.all()[:1].get()
        return PortfolioItem.objects.create(tenant=tenant, **validated_data)


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order"""

    class Meta:
        model = Order
        fields = (
            "id",
            "state",
            "owner",
            "order_request_sent_at",
            "created_at",
            "updated_at",
            "completed_at"
        )
        ordering = ["-created_at"]
        read_only_fields = ("created_at", "updated_at")

    def create(self, validated_data):
        tenant = Tenant.objects.all()[:1].get()
        return Order.objects.create(tenant=tenant, **validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem"""

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
            "owner",
            "external_url",
            "artifacts",
            "order_request_sent_at",
            "created_at",
            "updated_at",
            "completed_at"
        )
        ordering = ["-created_at"]
        read_only_fields = ("created_at", "updated_at")

    def create(self, validated_data):
        tenant = Tenant.objects.all()[:1].get()
        return OrderItem.objects.create(tenant=tenant, **validated_data)
