import django_rq
from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
)
from rest_framework import viewsets, status
from rest_framework.request import Request
from rest_framework.response import Response
from rq import job as rq_job

from automation_services_catalog.common.serializers import TaskSerializer
from automation_services_catalog.main.common import models
from automation_services_catalog.main.common import serializers
from automation_services_catalog.main.common import tasks


@extend_schema_view(
    retrieve=extend_schema(
        description="Get an existing group",
    ),
    list=extend_schema(
        description="List all groups",
    ),
)
class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.GroupSerializer
    ordering = ("name",)

    def get_queryset(self):
        roles = self.request.GET.getlist("role")
        if roles:
            queryset = models.Group.objects.filter(
                roles__name__in=roles
            ).distinct()
        else:
            queryset = models.Group.objects.all()
        return queryset


@extend_schema_view(
    create=extend_schema(
        description="Sync groups from keycloak. Returns a background task id.",
        responses={status.HTTP_200_OK: TaskSerializer},
        request=None,
    ),
)
class GroupSyncViewSet(viewsets.ViewSet):
    def create(self, request: Request):
        job = django_rq.enqueue(tasks.sync_external_groups)
        serializer = TaskSerializer(job)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


@extend_schema_view(
    retrieve=extend_schema(
        description="Get the status of a background task",
        responses={status.HTTP_202_ACCEPTED: TaskSerializer},
        parameters=[
            OpenApiParameter(
                "id",
                required=True,
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description="background task UUID",
            ),
        ],
    ),
)
class TaskViewSet(viewsets.ViewSet):
    def retrieve(self, request: Request, pk: str):
        try:
            job = rq_job.Job.fetch(pk, connection=django_rq.get_connection())
        except rq_job.NoSuchJobError:
            raise Http404
        return Response(TaskSerializer(job).data, status=status.HTTP_200_OK)
