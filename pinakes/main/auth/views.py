from django.contrib.auth import get_user_model
from django.contrib.auth import logout

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework import mixins
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)

from pinakes.common.auth.keycloak_django.clients import get_oidc_client
from pinakes.main.auth import serializers


@extend_schema_view(
    retrieve=extend_schema(
        description="Get the current login user",
        tags=["auth"],
        operation_id="me_retrieve",
    ),
)
class CurrentUserViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.CurrentUserSerializer
    model = get_user_model()

    def get_object(self):
        return self.request.user


@extend_schema_view(
    post=extend_schema(
        description="Logout current session",
        tags=["auth"],
        operation_id="logout_create",
    ),
)
class SessionLogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_serializer(self):
        return None

    def post(self, request):
        extra_data = request.keycloak_user.extra_data
        openid_client = get_oidc_client()
        openid_client.logout_user_session(
            extra_data["access_token"], extra_data["refresh_token"]
        )
        logout(request)
        return Response(status=status.HTTP_200_OK)
