""" pytest fixtures """
import urllib.parse
import pytest
import os
import re
import inspect
from unittest.mock import Mock

from django.urls import resolve, reverse
from django.contrib.auth.models import User

from rest_framework.test import APIRequestFactory, force_authenticate

DUMMY_ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJjOGhQcFdtSk0wWmxYcXRvcnNScVVwcC1GYWNiOTl6UU44NHkzWkpmS0J3In0.eyJleHAiOjE2NDM4MTYwNzksImlhdCI6MTY0MzgxNTc3OSwiYXV0aF90aW1lIjoxNjQzODE1Nzc5LCJqdGkiOiJkY2FhYzYzOC0zNDk4LTQ5YzctYjM3NC1mMjE2MTg3NDcyMTIiLCJpc3MiOiJodHRwOi8va2V5Y2xvYWsudm0ubG9jYWw6ODA4MC9hdXRoL3JlYWxtcy9hYXAiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiNzc3YmUyYWQtM2QyZi00ZWViLTliODgtZjhjNjViNWMxZDZkIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiY2F0YWxvZyIsIm5vbmNlIjoiTUxSemJPQ3FYTlU0MHp0ZFlLSnp6cTA4NUVRcnc4WElUbUxiVnpNblR2d0dvQVlTVXZRZ1piTVFYSllCbFNEbiIsInNlc3Npb25fc3RhdGUiOiIzNjk5ODJjNC03NTcxLTQ0MmYtODIwZC1iODJlZTRjZTFkMWQiLCJhY3IiOiIxIiwiYWxsb3dlZC1vcmlnaW5zIjpbImh0dHA6Ly9hcHA6ODAwMC8qIl0sInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIiwiZGVmYXVsdC1yb2xlcy1hYXAiXX0sInJlc291cmNlX2FjY2VzcyI6eyJjYXRhbG9nIjp7InJvbGVzIjpbImFwcHJvdmFsLWFkbWluIiwiY2F0YWxvZy1hZG1pbiJdfSwiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19fSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsInNpZCI6IjM2OTk4MmM0LTc1NzEtNDQyZi04MjBkLWI4MmVlNGNlMWQxZCIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwibmFtZSI6IkZyZWQgRmxpbnRzdG9uZSIsInByZWZlcnJlZF91c2VybmFtZSI6ImZyZWQiLCJnaXZlbl9uYW1lIjoiRnJlZCIsImZhbWlseV9uYW1lIjoiRmxpbnRzdG9uZSIsImVtYWlsIjoiZnJlZEBzbGF0ZXJvY2suY29tIn0.Nz1Ry8FUY2XCRQeVP-ihNAhaVKUELIsXYWKvlMyYRkHJBPQehtEgf5Chl_5HqcQ7QlxHtsg7jorB507z1kKoLsI6SXYBMBIMIPRF5CU2IqBv0yLxKnqp1u_pQdrnMcqNv3fPq2ZF0bE4ESYSUNTzglOE3A1jiIYf1H4BeK_Wyv44_SUuDQ0ghJHSCHWXhVtpStMczsnSfz_T7zja8QNaUO9lsz76DJZSXBfY3P8HYncsinw2H09wq58m5ZYpAIlN6HBifZ3v-VlHx2nSEITsL2ymBhz3HO8K7SAHnbakf_UTawTpDtYdqJSHce9-BPAU8M2bRzQ4Wa7U_O_S0R9-Mw"


@pytest.fixture
def normal_user():
    try:
        user = User.objects.get(username="normal")
    except User.DoesNotExist:
        user = User(username="normal", is_superuser=False, password="normal")
        user.save()
    return user


@pytest.fixture
def admin():
    try:
        user = User.objects.get(username="admin")
    except User.DoesNotExist:
        user = User(
            username="admin",
            is_superuser=True,
            password="admin",
            first_name="Ansible",
            last_name="Catalog",
        )
        user.save()
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
    ):
        curframe = inspect.currentframe()
        call_path = inspect.getouterframes(curframe, 2)[1][1]
        regex = "[/\\\\]main[/\\\\](.+)[/\\\\]tests[/\\\\]"
        namespace = re.search(regex, call_path).groups()[0]
        url = reverse(f"{namespace}:{pattern}", args=((id,) if id else None))
        view, view_args, view_kwargs = resolve(urllib.parse.urlparse(url)[2])
        request = getattr(APIRequestFactory(), verb)(
            url, data=data, format=format
        )
        request.session = Mock()
        if user and authenticated:
            force_authenticate(request, user=user)
        keycloak_mock = Mock()
        keycloak_mock.extra_data = {
            "id": "1",
            "access_token": DUMMY_ACCESS_TOKEN,
            "refresh_token": DUMMY_ACCESS_TOKEN,
        }
        request.keycloak_user = keycloak_mock
        response = view(request, *view_args, **view_kwargs)
        response.render()
        return response

    return rf


@pytest.fixture
def media_dir():
    base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, "automation_services_catalog/main/catalog/tests/data")


@pytest.fixture
def small_image():
    base_dir = os.path.dirname(__file__)
    image_path = os.path.join(
        base_dir, "automation_services_catalog/main/catalog/tests/data/redhat_icon.png"
    )

    with open(image_path, "rb") as f:
        yield f
        f.close()


@pytest.fixture
def another_image():
    base_dir = os.path.dirname(__file__)
    image_path = os.path.join(
        base_dir, "automation_services_catalog/main/catalog/tests/data/ansible_icon.png"
    )

    with open(image_path, "rb") as f:
        yield f
        f.close()
