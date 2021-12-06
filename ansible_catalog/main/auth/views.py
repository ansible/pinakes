import rq.job as rq_job
import django_rq
from django.http import Http404
from django.contrib.auth.models import User

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import mixins

from ansible_catalog.main.auth import models
from ansible_catalog.main.auth import tasks
from ansible_catalog.main.auth import serializers


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


class CurrentUserViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.CurrentUserSerializer

    def retrieve(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
