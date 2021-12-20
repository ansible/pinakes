""" Serializers for Catalog Model."""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

from ansible_catalog.main.models import Tenant, Image
from ansible_catalog.main.auth.models import Group
from ansible_catalog.main.catalog.models import (
    ApprovalRequest,
    ServicePlan,
    Order,
    OrderItem,
    Portfolio,
    PortfolioItem,
    ProgressMessage,
)


class TenantSerializer(serializers.ModelSerializer):
    """Tenant which groups login users"""

    class Meta:
        model = Tenant
        fields = (
            "id",
            "external_tenant",
        )


class PortfolioSerializer(serializers.ModelSerializer):
    """Portfolio which groups Portfolio Items"""

    icon_url = serializers.SerializerMethodField(
        "get_icon_url", allow_null=True
    )

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


class PortfolioItemInSerializer(serializers.Serializer):
    """Input parameters for creating a portfolio item"""

    service_offering_ref = serializers.CharField(
        required=True, help_text="Associated service offering id"
    )
    portfolio = serializers.IntegerField(
        required=True, help_text="ID of the portofolio"
    )


class CopyPortfolioSerializer(serializers.Serializer):
    """Parameters to copy a portfolio"""

    portfolio_name = serializers.CharField(
        help_text="New portfolio name", required=False
    )


class PortfolioItemSerializer(serializers.ModelSerializer):
    """PortfolioItem which maps to a Controller Job Template
    via the service_offering_ref"""

    icon_url = serializers.SerializerMethodField(
        "get_icon_url", allow_null=True
    )

    class Meta:
        model = PortfolioItem
        fields = (
            "id",
            "name",
            "description",
            "service_offering_ref",
            "service_offering_source_ref",
            "portfolio",
            "icon_url",
            "created_at",
            "updated_at",
        )

        read_only_fields = ("created_at", "updated_at")

    @extend_schema_field(OpenApiTypes.STR)
    def get_icon_url(self, obj):
        request = self.context.get("request")
        return (
            request.build_absolute_uri(obj.icon.file.url)
            if obj.icon is not None
            else None
        )


class CopyPortfolioItemSerializer(serializers.Serializer):
    """Parameters to copy a portfolio item"""

    portfolio_item_name = serializers.CharField(
        help_text="New portfolio item name", required=False
    )


class OrderItemFields:
    FIELDS = (
        "id",
        "name",
        "count",
        "service_parameters",
        "provider_control_parameters",
        "state",
        "portfolio_item",
        "order",
        "service_instance_ref",
        "inventory_service_plan_ref",
        "inventory_task_ref",
        "external_url",
        "owner",
        "order_request_sent_at",
        "created_at",
        "updated_at",
        "completed_at",
    )


class OrderItemExtraSerializer(serializers.Serializer):
    """
    Extra data for an order item including its portfolio item details,
    available only when query parameter extra=true
    """

    portfolio_item = PortfolioItemSerializer(many=False)


class OrderItemSerializer(serializers.ModelSerializer):
    """OrderItem which keeps track of an execution of Portfolio Item"""

    owner = serializers.ReadOnlyField()
    extra_data = serializers.SerializerMethodField(
        "get_extra_data", read_only=True, allow_null=True
    )

    class Meta:
        model = OrderItem
        fields = (
            *OrderItemFields.FIELDS,
            "artifacts",
            "extra_data",
        )
        read_only_fields = ("created_at", "updated_at", "order", "name")
        extra_kwargs = {
            "completed_at": {"allow_null": True},
            "order_request_sent_at": {"allow_null": True},
        }

    @extend_schema_field(OrderItemExtraSerializer(many=False))
    def get_extra_data(self, order_item):
        extra = self.context.get("request").GET.get("extra")
        if extra and extra.lower() == "true":
            serializer = OrderItemExtraSerializer(
                instance=order_item,
                many=False,
                context=self.context,
            )
            return serializer.data
        return None

    def create(self, validated_data):
        user = self.context["request"].user
        return OrderItem.objects.create(
            tenant=Tenant.current(), user=user, **validated_data
        )


class OrderItemDocSerializer(serializers.ModelSerializer):
    """Workaround for OrderItem list params in openapi spec"""

    class Meta:
        model = OrderItem
        fields = (*OrderItemFields.FIELDS,)
        read_only_fields = (
            "created_at",
            "updated_at",
            "order",
            "portfolio_item",
            "name",
        )


class OrderExtraSerializer(serializers.Serializer):
    """
    Extra data for an order including its order items,
    available only when query parameter extra=true
    """

    order_items = OrderItemSerializer(many=True)


class OrderSerializer(serializers.ModelSerializer):
    """Order which groups an order item and its before and after processes (To be added)"""

    owner = serializers.ReadOnlyField()
    extra_data = serializers.SerializerMethodField(
        "get_extra_data", allow_null=True, read_only=True
    )

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
            "extra_data",
        )
        read_only_fields = ("created_at", "updated_at")
        extra_kwargs = {
            "completed_at": {"allow_null": True},
            "order_request_sent_at": {"allow_null": True},
        }

    def create(self, validated_data):
        user = self.context["request"].user
        return Order.objects.create(
            tenant=Tenant.current(), user=user, **validated_data
        )

    @extend_schema_field(OrderExtraSerializer(many=False))
    def get_extra_data(self, order):
        extra = self.context.get("request").GET.get("extra")
        if extra and extra.lower() == "true":
            serializer = OrderExtraSerializer(
                instance=order, many=False, context=self.context
            )
            return serializer.data
        return None


class ImageSerializer(serializers.ModelSerializer):
    """An image file used as an icon for portfolio or portfolio item"""

    class Meta:
        model = Image
        fields = (
            "source_ref",
            "file",
        )


class ApprovalRequestSerializer(serializers.ModelSerializer):
    """ApprovalRequest which keeps track of the approval progress of an order"""

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
    """ProgressMessage which wraps a message describing the progress of an order or order item"""

    class Meta:
        model = ProgressMessage
        fields = (
            "received_at",
            "level",
            "message",
            "messageable_type",
            "messageable_id",
        )


class ServicePlanExtraSerializer(serializers.Serializer):
    """
    Extra data for a service plan including its base schema,
    available only when query parameter extra=true
    """

    base_schema = serializers.JSONField(
        read_only=True,
        allow_null=True,
        help_text="The base schema, same as schema if unmodified",
    )


class ServicePlanSerializer(serializers.ModelSerializer):
    """ServicePlan which describes parameters required for a portfolio item"""

    schema = serializers.JSONField(
        read_only=True,
        allow_null=True,
        help_text="The active schema of parameters for provisioning a portfolio item",
    )
    modified = serializers.BooleanField(
        read_only=True,
        help_text="Whether or not the schema has been modified by user",
    )
    outdated = serializers.BooleanField(
        read_only=True,
        help_text="Whether or not the base schema is outdated. The portfolio item is not orderable if the base schema is outdated.",
    )
    outdated_changes = serializers.ReadOnlyField(
        help_text="Changes of the base schema from inventory since last edit",
    )
    extra_data = serializers.SerializerMethodField(
        "get_extra_data", allow_null=True, read_only=True
    )

    class Meta:
        model = ServicePlan
        fields = (
            "id",
            "name",
            "schema",
            "modified",
            "outdated",
            "outdated_changes",
            "service_offering_ref",
            "inventory_service_plan_ref",
            "portfolio_item",
            "extra_data",
        )

    @extend_schema_field(ServicePlanExtraSerializer(many=False))
    def get_extra_data(self, service_plan):
        extra = self.context.get("request").GET.get("extra")
        if extra and extra.lower() == "true":
            serializer = ServicePlanExtraSerializer(
                instance=service_plan, many=False, context=self.context
            )
            return serializer.data
        return None


class ModifiedServicePlanInSerializer(serializers.Serializer):
    """Paramters to update a modified service plan"""

    modified = serializers.JSONField(
        required=True, help_text="The new modified schema for the service plan"
    )


class SharingRequestSerializer(serializers.Serializer):
    """SharingRequest which defines groups and permissions that the object can be shared to"""

    permissions = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        help_text="List of permissions (e.g. `read`, `update`, `delete`).",
    )
    groups = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Group.objects.all(), help_text="List of group IDs."
    )

    def validate_permissions(self, value):
        valid_scopes = self.context.get("valid_scopes", [])
        invalid_scopes = set(value).difference(valid_scopes)
        if invalid_scopes:
            raise serializers.ValidationError(
                "Unexpected permissions: {}".format(", ".join(invalid_scopes))
            )
        return value


class SharingPermissionSerializer(serializers.Serializer):
    """Sharing permissions which were applied to a group"""

    permissions = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        help_text="List of permissions (e.g. `read`, `update`, `delete`).",
    )
    group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), help_text="Group ID"
    )
