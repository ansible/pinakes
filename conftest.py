""" pytest fixtures """
import contextlib
import os
import urllib.parse
from unittest import mock

import pytest

from django.urls import resolve, reverse
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory, force_authenticate

from pinakes.common.auth.keycloak.models import (
    AuthzResource,
    AuthzPermission,
)
from pinakes.common.auth.keycloak_django.permissions import (
    WILDCARD_RESOURCE_ID,
)
from pinakes.common.auth.keycloak_django.utils import (
    parse_scope_name,
    make_resource_name,
)

AUTHZ_CLIENT_CLASS = "pinakes.common.auth.keycloak_django.clients.AuthzClient"


# FIXME(cutwater): Replace this base64 blob with human readable payload
#  which is encoded into JWT when needed.
DUMMY_ACCESS_TOKEN = (
    "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJjOGhQcFdtSk0wWmxYcXRvc"
    "nNScVVwcC1GYWNiOTl6UU44NHkzWkpmS0J3In0.eyJleHAiOjE2NDM4MTYwNzksImlhdCI6MT"
    "Y0MzgxNTc3OSwiYXV0aF90aW1lIjoxNjQzODE1Nzc5LCJqdGkiOiJkY2FhYzYzOC0zNDk4LTQ"
    "5YzctYjM3NC1mMjE2MTg3NDcyMTIiLCJpc3MiOiJodHRwOi8va2V5Y2xvYWsudm0ubG9jYWw6"
    "ODA4MC9hdXRoL3JlYWxtcy9hYXAiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiNzc3YmUyYWQtM"
    "2QyZi00ZWViLTliODgtZjhjNjViNWMxZDZkIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiY2F0YW"
    "xvZyIsIm5vbmNlIjoiTUxSemJPQ3FYTlU0MHp0ZFlLSnp6cTA4NUVRcnc4WElUbUxiVnpNblR"
    "2d0dvQVlTVXZRZ1piTVFYSllCbFNEbiIsInNlc3Npb25fc3RhdGUiOiIzNjk5ODJjNC03NTcx"
    "LTQ0MmYtODIwZC1iODJlZTRjZTFkMWQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbI"
    "mh0dHA6Ly9hcHA6ODAwMC8qIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2"
    "FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIiwiZGVmYXVsdC1yb2xlcy1hYXAiXX0sInJlc29"
    "1cmNlX2FjY2VzcyI6eyJjYXRhbG9nIjp7InJvbGVzIjpbImFwcHJvdmFsLWFkbWluIiwiY2F0"
    "YWxvZy1hZG1pbiJdfSwiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hb"
    "mFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgcH"
    "JvZmlsZSBlbWFpbCIsInNpZCI6IjM2OTk4MmM0LTc1NzEtNDQyZi04MjBkLWI4MmVlNGNlMWQ"
    "xZCIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwibmFtZSI6IkZyZWQgRmxpbnRzdG9uZSIsInBy"
    "ZWZlcnJlZF91c2VybmFtZSI6ImZyZWQiLCJnaXZlbl9uYW1lIjoiRnJlZCIsImZhbWlseV9uY"
    "W1lIjoiRmxpbnRzdG9uZSIsImVtYWlsIjoiZnJlZEBzbGF0ZXJvY2suY29tIn0.Nz1Ry8FUY2"
    "XCRQeVP-ihNAhaVKUELIsXYWKvlMyYRkHJBPQehtEgf5Chl_5HqcQ7QlxHtsg7jorB507z1kK"
    "oLsI6SXYBMBIMIPRF5CU2IqBv0yLxKnqp1u_pQdrnMcqNv3fPq2ZF0bE4ESYSUNTzglOE3A1j"
    "iIYf1H4BeK_Wyv44_SUuDQ0ghJHSCHWXhVtpStMczsnSfz_T7zja8QNaUO9lsz76DJZSXBfY3"
    "P8HYncsinw2H09wq58m5ZYpAIlN6HBifZ3v-VlHx2nSEITsL2ymBhz3HO8K7SAHnbakf_UTaw"
    "TpDtYdqJSHce9-BPAU8M2bRzQ4Wa7U_O_S0R9-Mw"
)


@pytest.fixture
def normal_user():
    user, _ = User.objects.get_or_create(
        username="normal",
        defaults=dict(is_superuser=False, password="normal"),
    )
    return user


@pytest.fixture
def admin():
    user, _ = User.objects.get_or_create(
        username="admin",
        defaults=dict(
            is_superuser=True,
            password="admin",
            first_name="Ansible",
            last_name="Catalog",
        ),
    )
    return user


@pytest.fixture
def api_request(admin):
    def rf(
        verb,
        pattern,
        id=None,
        data=None,
        user=admin,
        format="json",
        authenticated=True,
        rbac_enabled=False,
    ):
        url = reverse(pattern, args=((id,) if id else None))
        view, view_args, view_kwargs = resolve(urllib.parse.urlparse(url)[2])
        request = getattr(APIRequestFactory(), verb)(
            url, data=data, format=format
        )
        request.session = mock.Mock()
        if user and authenticated:
            force_authenticate(request, user=user)

        keycloak_mock = mock.Mock()
        keycloak_mock.extra_data = {
            "id": "1",
            "access_token": DUMMY_ACCESS_TOKEN,
            "refresh_token": DUMMY_ACCESS_TOKEN,
        }
        request.keycloak_user = keycloak_mock

        if rbac_enabled:
            authz_client_mock = contextlib.nullcontext()
        else:
            authz_client_mock = patch_authz_client()

        with authz_client_mock:
            response = view(request, *view_args, **view_kwargs)
            response.render()

        return response

    return rf


@pytest.fixture
def media_dir():
    base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, "pinakes/main/catalog/tests/data")


@pytest.fixture
def small_image():
    base_dir = os.path.dirname(__file__)
    image_path = os.path.join(
        base_dir,
        "pinakes/main/catalog/tests/data/redhat_icon.png",
    )

    with open(image_path, "rb") as f:
        yield f


@pytest.fixture
def another_image():
    base_dir = os.path.dirname(__file__)
    image_path = os.path.join(
        base_dir,
        "pinakes/main/catalog/tests/data/ansible_icon.png",
    )

    with open(image_path, "rb") as f:
        yield f


class AuthzClientMock:
    def get_permissions(self, permissions=None):
        if permissions is None:
            return []

        if isinstance(permissions, AuthzPermission):
            permissions = [permissions]

        resources = []
        for p in permissions:
            resource_type, _ = parse_scope_name(p.scope)
            resources.append(
                AuthzResource(
                    rsid="00000000-0000-0000-0000-000000000000",
                    rsname=make_resource_name(
                        resource_type, WILDCARD_RESOURCE_ID
                    ),
                    scopes=[p.scope],
                )
            )
        return resources

    def check_permissions(self, permissions=None) -> bool:
        return True


def patch_authz_client():
    return mock.patch(AUTHZ_CLIENT_CLASS, return_value=AuthzClientMock())
