"""Serializers for Catalog Model."""
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

from pinakes.common.fields import MetadataField
from pinakes.main.models import Tenant, Image
from pinakes.main.validators import UniqueWithinTenantValidator
from pinakes.main.common.models import Group
from pinakes.main.catalog.models import (
    ApprovalRequest,
    ServicePlan,
    Order,
    OrderItem,
    Portfolio,
    PortfolioItem,
    ProgressMessage,
)
from pinakes.main.catalog.services.create_portfolio_item import (
    CreatePortfolioItem,
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

    metadata = MetadataField(help_text="JSON Metadata about the portfolio")

    class Meta:
        model = Portfolio
        validators = [
            UniqueWithinTenantValidator(
                queryset=Portfolio.objects.all(), fields=("name", "tenant")
            )
        ]
        fields = (
            "id",
            "name",
            "description",
            "metadata",
            "owner",
            "icon_url",
            "created_at",
            "updated_at",
        )
        ordering = ["-created_at"]
        read_only_fields = ("created_at", "updated_at")

    def create(self, validated_data):
        user = self.context["request"].user
        return Portfolio.objects.create(
            tenant=Tenant.current(), user=user, **validated_data
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

    def create(self, validated_data):
        return CreatePortfolioItem(validated_data).process().item


class CopyPortfolioSerializer(serializers.Serializer):
    """Parameters to copy a portfolio"""

    portfolio_name = serializers.CharField(
        help_text="New portfolio name", required=False
    )


class PortfolioItemSerializerBase(serializers.ModelSerializer):
    """PortfolioItem which maps to a Controller Job Template
    via the service_offering_ref"""

    icon_url = serializers.SerializerMethodField(
        "get_icon_url", allow_null=True
    )

    metadata = MetadataField(
        user_capabilities_field=None,
        help_text="JSON Metadata about the portfolio item",
    )

    class Meta:
        model = PortfolioItem
        fields = (
            "id",
            "name",
            "description",
            "service_offering_ref",
            "service_offering_source_ref",
            "metadata",
            "portfolio",
            "icon_url",
            "owner",
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


class PortfolioItemSerializer(PortfolioItemSerializerBase):
    metadata = MetadataField(
        help_text="JSON Metadata about the portfolio item"
    )


class CopyPortfolioItemSerializer(serializers.Serializer):
    """Parameters to copy a portfolio item"""

    portfolio_item_name = serializers.CharField(
        help_text="New portfolio item name", required=False
    )
    portfolio_id = serializers.CharField(
        help_text="The target portfolio which this item belongs to",
        required=False,
    )


ORDER_ITEM_FIELDS = (
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

    portfolio_item = PortfolioItemSerializerBase(many=False)


class UniqueWithinOrderValidator(UniqueWithinTenantValidator):
    """Uniqueness validator on joint columns including order"""

    def __call__(self, attrs, serializer):
        order_attr = False
        if "order" not in attrs:
            if "order_id" in serializer.context["view"].kwargs:
                attrs["order"] = Order.objects.get(
                    id=serializer.context["view"].kwargs["order_id"]
                )
                order_attr = True

        order_field = False
        if "order" not in serializer.fields:
            serializer.fields["order"] = serializers.PrimaryKeyRelatedField(
                queryset=Order.objects.all()
            )
            order_field = True

        name_attr = False
        if "name" not in attrs:
            if "portfolio_item" in attrs:
                attrs["name"] = attrs["portfolio_item"].name
                name_attr = True

        super().__call__(attrs, serializer)

        if order_attr:
            del attrs["order"]

        if order_field:
            del serializer.fields["order"]

        if name_attr:
            del attrs["name"]


class OrderItemSerializerBase(serializers.ModelSerializer):
    """OrderItem which keeps track of an execution of Portfolio Item"""

    owner = serializers.ReadOnlyField()
    state = serializers.SerializerMethodField()
    extra_data = serializers.SerializerMethodField(
        "get_extra_data", read_only=True, allow_null=True
    )
    metadata = MetadataField(
        user_capabilities_field=None,
        help_text="Order item metadata",
    )

    class Meta:
        model = OrderItem
        validators = [
            UniqueWithinOrderValidator(
                queryset=OrderItem.objects.all(),
                fields=("name", "order", "portfolio_item", "tenant"),
            )
        ]
        fields = (
            *ORDER_ITEM_FIELDS,
            "artifacts",
            "extra_data",
            "metadata",
        )
        read_only_fields = ("created_at", "updated_at", "order", "name")
        extra_kwargs = {
            "completed_at": {"allow_null": True},
            "order_request_sent_at": {"allow_null": True},
        }

    def get_state(self, obj):
        return _(obj.state)

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


class OrderItemSerializer(OrderItemSerializerBase):
    metadata = MetadataField(help_text="Order item metadata")


class OrderItemDocSerializer(serializers.ModelSerializer):
    """Workaround for OrderItem list params in openapi spec"""

    class Meta:
        model = OrderItem
        fields = ORDER_ITEM_FIELDS
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

    order_items = OrderItemSerializerBase(many=True)


class OrderSerializer(serializers.ModelSerializer):
    """Order which groups an order item and its before
    and after processes (To be added)"""

    owner = serializers.ReadOnlyField()
    state = serializers.SerializerMethodField()
    extra_data = serializers.SerializerMethodField(
        "get_extra_data", allow_null=True, read_only=True
    )

    metadata = MetadataField(help_text="Order metadata")

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
            "metadata",
        )
        read_only_fields = ("created_at", "updated_at")
        extra_kwargs = {
            "completed_at": {"allow_null": True},
            "order_request_sent_at": {"allow_null": True},
        }

    def get_state(self, obj):
        return _(obj.state)

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
    """ApprovalRequest which keeps track of the approval
    progress of an order"""

    state = serializers.SerializerMethodField()
    reason = serializers.SerializerMethodField()

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
        extra_kwargs = {
            "request_completed_at": {"allow_null": True},
        }

    def get_state(self, obj):
        return _(obj.state)

    def get_reason(self, obj):
        return _(obj.reason)


class ProgressMessageSerializer(serializers.ModelSerializer):
    """ProgressMessage which wraps a message describing
    the progress of an order or order item"""

    level = serializers.SerializerMethodField()
    message = serializers.SerializerMethodField()
    messageable_type = serializers.SerializerMethodField()

    gettext_noop("Order")
    gettext_noop("OrderItem")

    class Meta:
        model = ProgressMessage
        fields = (
            "received_at",
            "level",
            "message",
            "messageable_type",
            "messageable_id",
        )

    def get_level(self, obj):
        return _(obj.level)

    def get_messageable_type(self, obj):
        return _(obj.messageable_type)

    def get_message(self, obj):
        return (
            _(obj.message) % obj.message_params
            if bool(obj.message_params)
            else _(obj.message)
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

    id = serializers.IntegerField(
        read_only=True,
        allow_null=True,
        help_text=(
            "ID of the service plan. Can be null if the service plan has not"
            " been imported for editing"
        ),
    )
    schema = serializers.JSONField(
        read_only=True,
        allow_null=True,
        help_text=(
            "The active schema of parameters for provisioning a portfolio item"
        ),
    )
    modified = serializers.BooleanField(
        read_only=True,
        help_text="Whether or not the schema has been modified by user",
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
    """SharingRequest which defines groups and permissions
    that the object can be shared to"""

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
    group_id = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), help_text="Group ID"
    )

    group_name = serializers.CharField(help_text="Group Name")


class NextNameInSerializer(serializers.Serializer):
    """Paramters to retrieve next available portfolio item name"""

    portfolio_item_id = serializers.IntegerField(
        required=True,
        help_text="ID of the portfolio item.",
    )
    destination_portfolio_id = serializers.IntegerField(
        read_only=True,
        required=False,
        help_text="ID of the destination portfolio.",
    )


class NextNameOutSerializer(serializers.Serializer):
    """Next available portfolio item name"""

    next_name = serializers.CharField(
        max_length=64, help_text="Next available portfolio item name"
    )
