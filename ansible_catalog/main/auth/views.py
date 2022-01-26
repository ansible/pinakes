import rq.job as rq_job
import django_rq
from django.http import Http404
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth import logout

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import mixins
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
)

from ansible_catalog.main.auth import models
from ansible_catalog.main.auth import tasks
from ansible_catalog.main.auth import serializers
from ansible_catalog.common.serializers import TaskSerializer
from ansible_catalog.common.auth.keycloak.openid import OpenIdConnect


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

    def get_queryset(self):
        roles = self.request.GET.getlist("role[]")
        if roles:
            queryset = models.Group.objects.filter(roles__name__in=roles).distinct()
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


@extend_schema_view(
    retrieve=extend_schema(
        description="Get the current login user",
    ),
)
class CurrentUserViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.CurrentUserSerializer
    model = User

    def get_object(self):
        return self.request.user


class SessionLogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_serializer(self):
        return None

    def post(self, request):
        extra_data = request.keycloak_user.extra_data
        openid_client = OpenIdConnect(
            settings.KEYCLOAK_URL,
            settings.KEYCLOAK_REALM,
            settings.KEYCLOAK_CLIENT_ID,
            settings.KEYCLOAK_CLIENT_SECRET,
        )
        openid_client.logout_user_session(
            extra_data["access_token"], extra_data["refresh_token"]
        )
        logout(request)
        return Response(status=status.HTTP_200_OK)
