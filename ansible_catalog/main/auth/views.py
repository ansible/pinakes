import rq.job as rq_job
import django_rq
from django.contrib.auth import logout
from django.http import Http404

from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ansible_catalog.main.auth import models
from ansible_catalog.main.auth import tasks
from ansible_catalog.main.auth import serializers
from ansible_catalog.common.auth.keycloak_django.clients import (
    get_admin_client,
)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Group.objects.all()
    serializer_class = serializers.GroupSerializer


class GroupSyncViewSet(viewsets.ViewSet):
    def create(self, request: Request):
        job = django_rq.enqueue(tasks.sync_external_groups)
        return Response({"id": job.id}, status=status.HTTP_202_ACCEPTED)

    def retrieve(self, request: Request, pk: str):
        try:
            job = rq_job.Job.fetch(pk, connection=django_rq.get_connection())
        except rq_job.NoSuchJobError:
            raise Http404
        return Response({"id": job.id, "status": job.get_status()})


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        social_auth_id = request.keycloak_user.extra_data["id"]
        client = get_admin_client()
        client.logout_user(social_auth_id)
        logout(request)
        return Response(status=status.HTTP_200_OK)
