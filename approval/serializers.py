""" Serializers for Approval Model."""
from rest_framework import serializers
from decimal import Decimal

from .basemodel import Tenant
from .models import (
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

    def create(self, validated_data):
        return Template.objects.create(tenant=Tenant.current(), **validated_data)


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
        read_only_fields = ("created_at", "updated_at")

    def create(self, validated_data):
        max_obj = Workflow.objects.filter(tenant=Tenant.current()).order_by('-internal_sequence').first()
        if max_obj is None:
            next_seq = Decimal(1)
        else:
            next_seq = Decimal(max_obj.internal_sequence.to_integral_value() + 1)
        return Workflow.objects.create(tenant=Tenant.current(), internal_sequence=next_seq, **validated_data)


class RequestSerializer(serializers.ModelSerializer):
    """Serializer for Request"""

    class Meta:
        model = Request
        fields = (
            "id",
            "requester_name",
            "name",
            "description",
            "workflow",
            "state",
            "decision",
            "reason",
            "parent",
            "number_of_children",
            "number_of_finished_children",
            "created_at",
            "notified_at",
            "finished_at",
        )

    def create(self, validate_data):
        return Request.objects.create(tenant=Tenant.current(), **validate_data)


class RequestInSerializer(serializers.Serializer):
    """Serializer for RequestIn"""
    name = serializers.CharField(required=True)
    description = serializers.CharField()
    content = serializers.JSONField()

    def create(self, validate_data):
        content = validate_data.pop("content")
        request_context = RequestContext.objects.create(content=content, context={})
        return Request.objects.create(
            tenant=Tenant.current(),
            request_context=request_context,
            **validate_data
        )


class ActionSerializer(serializers.ModelSerializer):
    """Serializer for Action"""

    class Meta:
        model = Action
        ordering = ["-created_at"]
        fields = (
            "id",
            "created_at",
            "request",
            "processed_by",
            "operation",
            "comments",
        )

    def create(self, validated_data):
        return Action.objects.create(tenant=Tenant.current(), **validated_data)
