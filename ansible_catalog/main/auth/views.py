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
from rest_framework.permissions import IsAuthenticated

from ansible_catalog.main.auth import models
from ansible_catalog.main.auth import tasks
from ansible_catalog.main.auth import serializers
from ansible_catalog.common.auth.keycloak.openid import OpenIdConnect


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
    model = User

    def get_object(self):
        return self.request.user


class SessionLogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        extra_data = request.keycloak_user.extra_data
        openid_client = OpenIdConnect(
            settings.KEYCLOAK_URL,
            settings.KEYCLOAK_REALM,
            settings.KEYCLOAK_CLIENT_ID,
            settings.KEYCLOAK_CLIENT_SECRET,
            extra_data["access_token"],
        )
        openid_client.logout_user_session(
            extra_data["refresh_token"],
        )
        logout(request)
        return Response(status=status.HTTP_200_OK)
