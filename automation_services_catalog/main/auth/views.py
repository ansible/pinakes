from django.contrib.auth.models import User
from django.conf import settings
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

from automation_services_catalog.main.auth import serializers
from automation_services_catalog.common.auth.keycloak.openid import (
    OpenIdConnect,
)


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
