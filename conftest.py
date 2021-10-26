""" pytest fixtures """
import urllib.parse
import pytest
import os
import re
import inspect

from django.urls import resolve, reverse
from django.contrib.auth.models import User

from rest_framework.test import APIRequestFactory, force_authenticate


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
        user = User(username="admin", is_superuser=True, password="admin")
        user.save()
    return user


@pytest.fixture
def api_request(admin):
    def rf(verb, pattern, id=None, data=None, user=admin, format="json"):
        curframe = inspect.currentframe()
        call_path = inspect.getouterframes(curframe, 2)[1][1]
        regex = "[/\\\\]main[/\\\\](.+)[/\\\\]tests[/\\\\]"
        namespace = re.search(regex, call_path).groups()[0]
        url = reverse(f"{namespace}:{pattern}", args=((id,) if id else None))
        view, view_args, view_kwargs = resolve(urllib.parse.urlparse(url)[2])
        request = getattr(APIRequestFactory(), verb)(
            url, data=data, format=format
        )
        if user:
            force_authenticate(request, user=user)
        response = view(request, *view_args, **view_kwargs)
        response.render()
        return response

    return rf


@pytest.fixture
def media_dir():
    base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, "ansible_catalog/media")


@pytest.fixture
def small_image():
    base_dir = os.path.dirname(__file__)
    image_path = os.path.join(
        base_dir, "ansible_catalog/main/catalog/tests/data/redhat_icon.png"
    )

    with open(image_path, "rb") as f:
        yield f
        f.close()
