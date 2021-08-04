""" pytest fixtures """
import urllib.parse
import pytest

from django.urls import resolve
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
    def rf(verb, url, data=None, user=admin):
        view, view_args, view_kwargs = resolve(urllib.parse.urlparse(url)[2])
        request = getattr(APIRequestFactory(), verb)(
            url, data=data, format="json"
        )
        if user:
            force_authenticate(request, user=user)
        response = view(request, *view_args, **view_kwargs)
        response.render()
        return response

    return rf
