from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.utils.translation import gettext_lazy as _

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework import mixins
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
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


class SessionLogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        description="Logout current session",
        tags=["auth"],
        operation_id="logout_create",
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                description="Logout successful"
            )
        },
    )
    def post(self, request):
        get_social_user = getattr(
            request.successful_authenticator, "get_social_user", None
        )
        if get_social_user is None:
            return Response(
                data={
                    "detail": _("Logout is not supported with Bearer auth.")
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        extra_data = get_social_user(request).extra_data
        openid_client = get_oidc_client()
        openid_client.logout_user_session(
            extra_data["access_token"], extra_data["refresh_token"]
        )
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)
