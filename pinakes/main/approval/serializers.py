"""Serializers for Approval Model."""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

from pinakes.common.fields import MetadataField, UserCapabilitiesField
from pinakes.main.approval.models import (
    NotificationSetting,
    NotificationType,
    Template,
    Workflow,
    Request,
    Action,
)
from pinakes.main.approval.permissions import WorkflowPermission
from pinakes.main.approval.services.create_action import (
    CreateAction,
)
from pinakes.main.approval import validations
from pinakes.main.validators import UniqueWithinTenantValidator


class NotificationTypeSerializer(serializers.ModelSerializer):
    """Notification type that define what settings are expected"""

    icon_url = serializers.SerializerMethodField(
        "get_icon_url", allow_null=True
    )

    class Meta:
        model = NotificationType
        fields = ("id", "n_type", "setting_schema", "icon_url")

    @extend_schema_field(OpenApiTypes.STR)
    def get_icon_url(self, obj):
        """get the url to fetch the icon"""
        request = self.context.get("request")
        return (
            request.build_absolute_uri(obj.icon.file.url)
            if obj.icon is not None
            else None
        )


class NotificationSettingSerializer(serializers.ModelSerializer):
    """Notification setting that stores settings for notification"""

    settings = serializers.JSONField(
        required=False,
        help_text="Parameters for configuring the notification method",
    )

    class Meta:
        model = NotificationSetting
        validators = [
            UniqueWithinTenantValidator(
                queryset=NotificationSetting.objects.all(),
                fields=("name", "tenant"),
            )
        ]
        fields = ("id", "name", "notification_type", "settings")


class TemplateSerializer(serializers.ModelSerializer):
    """The template to categorize workflows"""

    class Meta:
        model = Template
        validators = [
            UniqueWithinTenantValidator(
                queryset=Template.objects.all(), fields=("title", "tenant")
            )
        ]
        fields = (
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "process_method",
            "signal_method",
        )
        read_only_fields = ("created_at", "updated_at")


class GroupRefSerializer(serializers.Serializer):
    """RBAC group reference"""

    name = serializers.CharField(
        required=True, help_text="Name of the RBAC group"
    )
    uuid = serializers.CharField(
        required=True, help_text="UUID of the RBAC group"
    )


@extend_schema_field(GroupRefSerializer(many=True))
class GroupRefsField(serializers.JSONField):
    pass


class WorkflowSerializer(serializers.ModelSerializer):
    """
    The workflow to process approval requests.
    Each workflow can be linked to multiple groups of approvers.
    """

    group_refs = GroupRefsField(
        required=False,
        help_text=(
            "Array of RBAC groups associated with workflow. The groups need to"
            " have approval permission"
        ),
    )

    class Meta:
        model = Workflow
        fields = (
            "id",
            "name",
            "description",
            "template",
            "group_refs",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate_group_refs(self, value):
        serializer = GroupRefSerializer(many=True, data=value)
        serializer.is_valid(raise_exception=True)
        return validations.validate_approver_groups(value)


PLACEMENT_CHOICES = (
    ("top", "top"),
    ("bottom", "bottom"),
)


class RepositionSerializer(serializers.Serializer):
    """
    The desired increment relative to its current position,
    or placement to top or bottom of the list.
    """

    increment = serializers.IntegerField(
        required=False,
        write_only=True,
        help_text=(
            "Move the record up (negative) or down (positive) in the list. "
            "Upper workflows will be executed before lower ones"
            "Do not set it if placement is used"
        ),
    )
    placement = serializers.ChoiceField(
        required=False,
        choices=PLACEMENT_CHOICES,
        help_text=(
            "Place the record to the top or bottom of the list. The top "
            "workflow will be executed first. Do not set it if increment "
            "is used"
        ),
    )

    def validate(self, data):
        has_increment = "increment" in data
        has_placement = "placement" in data
        if has_increment and has_placement:
            raise serializers.ValidationError(
                {"increment and placement": "cannot both present in the body"}
            )
        if has_increment or has_placement:
            return data
        raise serializers.ValidationError(
            {"increment or placement": "either one is needed in the body"}
        )


class TagResourceSerializer(serializers.Serializer):
    """Resource with tags"""

    app_name = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Name of the application that the resource belongs to",
    )
    object_type = serializers.CharField(
        required=True, write_only=True, help_text="Type of the resource"
    )
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        write_only=True,
        help_text="An array of tags that the resource is tagged with",
    )


class ActionSerializer(serializers.ModelSerializer):
    """An action that changes the state of a request"""

    processed_by = serializers.CharField(
        read_only=True,
        help_text="The person who performs the action",
        default="",
    )

    comments = serializers.CharField(
        help_text="Comments for the action",
        default="",
    )

    class Meta:
        model = Action
        fields = (
            "id",
            "created_at",
            "request",
            "processed_by",
            "operation",
            "comments",
        )
        read_only_fields = ("created_at", "request")

    def create(self, validated_data):
        request = validated_data.pop("request")
        return CreateAction(request, validated_data).process().action


class RequestCapabilitiesField(UserCapabilitiesField):
    """Customized user capabilities for requests"""

    def to_representation(self, value):
        permissions = super().to_representation(value)
        return {**permissions, **self._valid_actions(permissions, value)}

    def _valid_actions(self, permissions, request: Request):
        if not permissions.get("retrieve"):
            return {}

        valid_actions = {}

        admin = self._is_admin()
        owner = self._is_owner(request)
        if admin or owner:
            valid_actions["cancel"] = request.can_cancel()
        if admin or not owner:
            valid_actions["memo"] = True
            valid_actions["approve"] = request.can_decide()
            valid_actions["deny"] = valid_actions["approve"]
        return valid_actions

    def _is_admin(self):
        """
        We currently cannot determine roles. Sine only admin can see workflows,
        we use workflow permission to assess
        """
        return WorkflowPermission().has_permission(
            self.context["request"], self.context["view"]
        )

    def _is_owner(self, request: Request):
        view = self.context["view"]
        return request.user == view.request.user


class RequestFields:
    FIELDS = (
        "id",
        "requester_name",
        "group_name",
        "owner",
        "name",
        "description",
        "parent",
        "workflow",
        "state",
        "decision",
        "reason",
        "created_at",
        "notified_at",
        "finished_at",
    )


class SubrequestSerializer(serializers.ModelSerializer):
    """
    Subrequest that has a parent but no no child requests.
    Actions are included.
    """

    owner = serializers.CharField(
        read_only=True,
        help_text="Identification of whom made the request",
        default="",
    )
    requester_name = serializers.CharField(
        read_only=True, help_text="Full name of the requester", default=""
    )
    actions = ActionSerializer(
        many=True,
        read_only=True,
        help_text="Actions that have done to the request",
    )

    class Meta:
        model = Request
        fields = (
            *RequestFields.FIELDS,
            "actions",
        )
        read_only_fields = (
            "__all__",
            "requester_name",
            "owner",
        )
        extra_kwargs = {
            "notified_at": {"allow_null": True},
            "finished_at": {"allow_null": True},
        }


class RequestExtraSerializer(serializers.Serializer):
    """
    Extra data for a request including its subrequests and actions,
    available only when query parameter extra=true
    """

    actions = ActionSerializer(many=True)
    subrequests = SubrequestSerializer(many=True)


class RequestSerializer(serializers.ModelSerializer):
    """
    Approval request.
    It may have child requests.
    Only a leaf node request can have workflow ID.
    """

    owner = serializers.CharField(
        read_only=True,
        help_text="Identification of whom made the request",
        default="",
    )
    requester_name = serializers.CharField(
        read_only=True, help_text="Full name of the requester", default=""
    )
    extra_data = serializers.SerializerMethodField(
        "get_extra_data", read_only=True, allow_null=True
    )
    metadata = MetadataField(
        user_capabilities_field=RequestCapabilitiesField(),
        help_text="JSON Metadata about the request",
    )

    class Meta:
        model = Request
        fields = (
            *RequestFields.FIELDS,
            "number_of_children",
            "number_of_finished_children",
            "extra_data",
            "metadata",
        )
        read_only_fields = (
            "__all__",
            "requester_name",
            "owner",
        )
        extra_kwargs = {
            "notified_at": {"allow_null": True},
            "finished_at": {"allow_null": True},
        }

    @extend_schema_field(RequestExtraSerializer(many=False))
    def get_extra_data(self, parent_request):
        extra = self.context.get("request").GET.get("extra")
        if extra and extra.lower() == "true":
            serializer = RequestExtraSerializer(
                instance=parent_request,
                many=False,
                context=self.context,
            )
            return serializer.data
        return None


class ResourceObjectSerializer(serializers.Serializer):
    """Resource object definition"""

    app_name = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Name of the application that the object belongs to",
    )
    object_type = serializers.CharField(
        required=True, write_only=True, help_text="Object type"
    )
    object_id = serializers.CharField(
        required=True, write_only=True, help_text="ID of the object"
    )
