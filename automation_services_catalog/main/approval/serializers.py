"""Serializers for Approval Model."""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from automation_services_catalog.main.approval.models import (
    Template,
    Workflow,
    Request,
    Action,
)
from automation_services_catalog.main.approval.services.create_request import (
    CreateRequest,
)
from automation_services_catalog.main.approval.services.create_action import (
    CreateAction,
)
from automation_services_catalog.main.approval import validations


class TemplateSerializer(serializers.ModelSerializer):
    """The template to categorize workflows"""

    class Meta:
        model = Template
        fields = ("id", "title", "description", "created_at", "updated_at")
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
        help_text="Array of RBAC groups associated with workflow. The groups need to have approval permission",
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
        read_only_fields = ("created_at", "updated_at", "template")

    def validate_group_refs(self, value):
        serializer = GroupRefSerializer(many=True, data=value)
        serializer.is_valid(raise_exception=True)
        return validations.validate_approver_groups(value)


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


class RequestFields:
    FIELDS = (
        "id",
        "requester_name",
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

    class Meta:
        model = Request
        fields = (
            *RequestFields.FIELDS,
            "number_of_children",
            "number_of_finished_children",
            "extra_data",
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


class RequestInSerializer(serializers.Serializer):
    """Input parameters for approval request object"""

    name = serializers.CharField(
        required=True, help_text="Name of the the request to be created"
    )
    description = serializers.CharField(
        required=False, help_text="Describe the request in more details"
    )
    content = serializers.JSONField(
        required=True, help_text="Content of the request in JSON format"
    )
    tag_resources = serializers.ListField(
        child=TagResourceSerializer(many=False),
        required=False,
        help_text="An array of resource tags that determine the workflows for the request",
    )

    def create(self, validated_data):
        return CreateRequest(validated_data).process().request


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
