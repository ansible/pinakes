"""pytest fixtures"""
import contextlib
import os
import urllib.parse
from unittest import mock

import jwt
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
DUMMY_ACCESS_TOKEN = {
    "name": "Fred Sample",
    "preferred_username": "fred",
    "given_name": "Fred",
    "family_name": "Sample",
    "email": "fred@acme.com",
    "resource_access": {
        "pinakes": {
            "roles": [
                "approval-admin",
                "catalog-admin",
            ]
        }
    },
}


@pytest.fixture
def normal_user():
    user, _ = User.objects.get_or_create(
        username="normal",
        defaults={"is_superuser": False, "password": "normal"},
    )
    return user


@pytest.fixture
def admin():
    user, _ = User.objects.get_or_create(
        username="admin",
        defaults={
            "is_superuser": True,
            "password": "admin",
            "first_name": "Ansible",
            "last_name": "Catalog",
        },
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
            access_token = jwt.encode(DUMMY_ACCESS_TOKEN, "", algorithm="none")
            force_authenticate(request, user=user, token=access_token)

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
