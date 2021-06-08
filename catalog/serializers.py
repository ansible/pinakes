""" Serializers for Catalog Model."""
from rest_framework import serializers

from .basemodel import Tenant
from .models import Portfolio
from .models import PortfolioItem


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
