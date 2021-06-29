import logging

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.mixins import LoginRequiredMixin

from rest_framework_extensions.mixins import NestedViewSetMixin

from common.tag_mixin import TagMixin
from inventory.basemodel import Source
from inventory.models import (
    ServiceInventory,
    ServiceOffering,
    ServiceOfferingNode,
    ServicePlan
)
from inventory.serializers import (
    ServiceInventorySerializer,
    ServicePlanSerializer,
    ServiceOfferingSerializer,
    ServiceOfferingNodeSerializer,
    SourceSerializer
)
from inventory.task_utils.refresh_inventory import RefreshInventory

# Create your views here.
logger = logging.getLogger("inventory")

class SourceViewSet(LoginRequiredMixin, NestedViewSetMixin, ModelViewSet):
    queryset = Source.objects.all().order_by("created_at")
    serializer_class = SourceSerializer
    permission_classes = (IsAuthenticated,)

    http_method_names = ["get", "patch", "head"]

    @action(methods=["patch"], detail=True)
    def refresh(self, request, pk):
        source = get_object_or_404(Source, pk=pk)
        RefreshInventory(source.tenant_id, source.id).process()

        return Response(None, status=status.HTTP_204_NO_CONTENT)

class ServicePlanViewSet(LoginRequiredMixin, NestedViewSetMixin, ModelViewSet):
    queryset = ServicePlan.objects.all().order_by("created_at")
    serializer_class = ServicePlanSerializer
    permission_classes = (IsAuthenticated,)

    http_method_names = ["get", "head"]

class ServiceOfferingViewSet(LoginRequiredMixin, NestedViewSetMixin, ModelViewSet):
    queryset = ServiceOffering.objects.all().order_by("created_at")
    serializer_class = ServiceOfferingSerializer
    permission_classes = (IsAuthenticated,)

    http_method_names = ["get", "head"]

    # TODO:
    @action(methods=["post"], detail=True)
    def applied_inventories_tags(self, request, pk):
        return Response(status=status.HTTP_204_NO_CONTENT)

    # TODO:
    @action(methods=["post"], detail=True)
    def order(self, request, pk):
        return Response(status=status.HTTP_204_NO_CONTENT)

class ServiceOfferingNodeViewSet(LoginRequiredMixin, NestedViewSetMixin, ModelViewSet):
    queryset = ServiceOfferingNode.objects.all().order_by("created_at")
    serializer_class = ServiceOfferingNodeSerializer
    permission_classes = (IsAuthenticated,)

    http_method_names = ["get", "head"]

class ServiceInventoryViewSet(LoginRequiredMixin, TagMixin, NestedViewSetMixin, ModelViewSet):
    queryset = ServiceInventory.objects.all().order_by("created_at")
    serializer_class = ServiceInventorySerializer
    permission_classes = (IsAuthenticated,)

    http_method_names = ["get", "post", "head"]
