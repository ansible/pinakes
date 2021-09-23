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
    """Serializer for Template."""

    class Meta:
        model = Template
        fields = ("id", "title", "description", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class WorkflowSerializer(serializers.ModelSerializer):
    """Serializer for Workflow."""

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
    """Serializer for Request"""

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


class RequestInSerializer(serializers.Serializer):
    """Serializer for RequestIn"""

    name = serializers.CharField(required=True)
    description = serializers.CharField()
    content = serializers.JSONField()

    def create(self, validate_data):
        return CreateRequest(validate_data).process().request


class ActionSerializer(serializers.ModelSerializer):
    """Serializer for Action"""

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
    """Serializer for sub request with actions"""

    actions = ActionSerializer(many=True, read_only=True)

    class Meta:
        model = Request
        fields = (
            *RequestFields.FIELDS,
            "actions",
        )


class RequestCompleteSerializer(serializers.ModelSerializer):
    """Serializer for Request with actions and subrequests"""

    actions = ActionSerializer(many=True, read_only=True)
    subrequests = SubrequestSerializer(many=True, read_only=True)

    class Meta:
        model = Request
        fields = (
            *RequestFields.FIELDS,
            "actions",
            "subrequests",
        )


class ResourceObjectSerializer(serializers.ModelSerializer):
    """Serializer for Linking Workflow"""

    app_name = serializers.CharField(required=True, write_only=True)
    object_type = serializers.CharField(required=True, write_only=True)
    object_id = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = TagLink
        fields = (
            "object_type",
            "object_id",
            "app_name",
        )
