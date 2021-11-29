"""Serializers for Approval Model."""
from rest_framework import serializers

from ansible_catalog.main.approval.models import (
    Template,
    Workflow,
    Request,
    RequestContext,
    Action,
    TagLink,
)
from ansible_catalog.main.approval.services.create_request import CreateRequest
from ansible_catalog.main.approval.services.create_action import CreateAction


class TemplateSerializer(serializers.ModelSerializer):
    """The template to categorize workflows"""

    class Meta:
        model = Template
        fields = ("id", "title", "description", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class WorkflowSerializer(serializers.ModelSerializer):
    """
    The workflow to process approval requests.
    Each workflow can be linked to multiple groups of approvers.
    """

    class Meta:
        model = Workflow
        fields = (
            "id",
            "name",
            "description",
            "template",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at", "template")


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


class RequestFields:
    FIELDS = (
        "id",
        "requester_name",
        "owner",
        "name",
        "description",
        "workflow",
        "state",
        "decision",
        "reason",
        "number_of_children",
        "number_of_finished_children",
        "created_at",
        "notified_at",
        "finished_at",
    )


class RequestSerializer(serializers.ModelSerializer):
    """
    Approval request.
    It may have child requests.
    Only a leaf node request can have workflow_id.
    """

    owner = serializers.CharField(
        read_only=True,
        help_text="Identification of whom made the request",
        default="",
    )
    requester_name = serializers.CharField(
        read_only=True, help_text="Full name of the requester", default=""
    )

    class Meta:
        model = Request
        fields = (
            *RequestFields.FIELDS,
            "parent",
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

    def create(self, validate_data):
        return CreateRequest(validate_data).process().request


class ActionSerializer(serializers.ModelSerializer):
    """An action that changes the state of a request"""

    processed_by = serializers.CharField(
        read_only=True, help_text="The person who performs the action"
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

    def create(self, validate_data):
        request = validate_data.pop("request")
        return CreateAction(request, validate_data).process().action


class SubrequestSerializer(serializers.ModelSerializer):
    """
    Subrequest that has a parent but no no child requests.
    Actions are included in the view
    """

    owner = serializers.CharField(
        read_only=True, help_text="Identification of whom made the request"
    )
    requester_name = serializers.CharField(
        read_only=True, help_text="Full name of the requester"
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


class RequestCompleteSerializer(serializers.ModelSerializer):
    """A complete view of request with actions and subrequests"""

    owner = serializers.CharField(
        read_only=True, help_text="Identification of whom made the request"
    )
    requester_name = serializers.CharField(
        read_only=True, help_text="Full name of the requester"
    )
    actions = ActionSerializer(
        many=True,
        read_only=True,
        help_text="Actions that have done to the request",
    )
    subrequests = SubrequestSerializer(
        many=True,
        read_only=True,
        help_text="Sub requests created from the request",
    )

    class Meta:
        model = Request
        fields = (
            *RequestFields.FIELDS,
            "actions",
            "subrequests",
        )


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
