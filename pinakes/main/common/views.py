import django_rq
import yaml
import importlib.resources
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
)
from rest_framework import viewsets, status
from rest_framework.filters import (
    BaseFilterBackend,
    OrderingFilter,
    SearchFilter,
)
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rq import job as rq_job

from pinakes.common.serializers import TaskSerializer
from pinakes.main.common import models
from pinakes.main.common import serializers
from pinakes.main.common import tasks


class GroupFilterBackend(BaseFilterBackend):
    """
    Filter that selects groups by roles.
    """

    def filter_queryset(self, request, queryset, _view):
        roles = request.GET.getlist("role")
        if roles:
            return queryset.filter(roles__name__in=roles).distinct()
        return queryset


@extend_schema_view(
    retrieve=extend_schema(
        description="Get an existing group",
    ),
    list=extend_schema(
        description="List all groups",
        parameters=[
            OpenApiParameter(
                "role",
                type={"type": "array", "items": {"type": "string"}},
                description="Any RBAC roles the groups belong to",
                examples=[
                    OpenApiExample(
                        "Query by multiple roles",
                        value="role=approval-admin&role=catalog-admin",
                    )
                ],
            ),
        ],
    ),
)
class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.GroupSerializer
    queryset = models.Group.objects.all()
    filter_backends = (
        GroupFilterBackend,
        DjangoFilterBackend,
        OrderingFilter,
        SearchFilter,
    )
    ordering = ("name",)
    filterset_fields = ("name",)
    search_fields = ("name",)


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
        responses={status.HTTP_200_OK: TaskSerializer},
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


@extend_schema_view(
    get=extend_schema(
        description="Get product and version info",
        responses={status.HTTP_200_OK: serializers.AboutSerializer},
    ),
)
class AboutView(APIView):
    """View class for About"""

    def get(self, request, *args, **kwargs):
        """Returns product and version info"""

        text = importlib.resources.read_text("pinakes", "about.yml")
        about = yaml.safe_load(text)
        return Response(
            serializers.AboutSerializer(about).data,
            status=status.HTTP_200_OK,
        )
