""" Serializers for Approval Model."""
from rest_framework import serializers

from main.models import Tenant
from main.approval.models import (
    Template,
    Workflow,
    Request,
    RequestContext,
    Action,
)


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
        content = validate_data.pop("content")
        request_context = RequestContext.objects.create(
            content=content, context={}
        )
        return Request.objects.create(
            request_context=request_context, **validate_data
        )


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


class RequestCompleteSerializer(serializers.ModelSerializer):
    """Serializer for Request with nested actions and children"""

    actions = ActionSerializer(many=True, read_only=True)

    class Meta:
        model = Request
        fields = (
            *RequestFields.FIELDS,
            "actions",
            "sub_requests",
        )


RequestCompleteSerializer._declared_fields[
    "sub_requests"
] = RequestCompleteSerializer(many=True)
