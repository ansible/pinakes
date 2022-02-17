import pytest

from django.urls import reverse

from pinakes import urls


API_PREFIX = urls.API_PATH_PREFIX


@pytest.mark.parametrize(
    ("name", "url"),
    [
        ("auth:me", f"/{API_PREFIX}/auth/me/"),
        ("auth:login", f"/{API_PREFIX}/auth/login/"),
        ("auth:logout", f"/{API_PREFIX}/auth/logout/"),
    ],
)
def test_urls(name, url):
    assert reverse(name) == url
