"""asc URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import include, path
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularJSONAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
    get_relative_url,
)

from ansible_catalog.main.catalog.urls import (
    router as catalog_router,
    urls_views as catalog_views,
)
from ansible_catalog.main.approval.urls import (
    router as approval_router,
    urls_views as approval_views,
)
from ansible_catalog.main.inventory.urls import (
    router as inventory_router,
    urls_views as inventory_views,
)


def _filter_by_view(urls_views, pattern):
    name = pattern.name
    if name in urls_views:
        if urls_views[name] == None:
            return False
        pattern.callback = urls_views[name]
    return True


API_PATH_PREFIX = settings.CATALOG_API_PATH_PREFIX.strip("/")
API_VER = "v1"
api_prefix = f"{API_PATH_PREFIX}/{API_VER}/"

approval_urls = [
    p for p in approval_router.urls if _filter_by_view(approval_views, p)
]
catalog_urls = [
    p for p in catalog_router.urls if _filter_by_view(catalog_views, p)
]
inventory_urls = [
    p for p in inventory_router.urls if _filter_by_view(inventory_views, p)
]

urlpatterns = [
    path(
        f"{api_prefix}schema/openapi.json",
        SpectacularJSONAPIView.as_view(),
        name="schema",
    ),
    path(
        f"{api_prefix}schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        f"{api_prefix}schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    # path("", include((api_urls, "api"), "catalog")),
    path(api_prefix, include((approval_urls, "api"), namespace="approval")),
    path(api_prefix, include((catalog_urls, "api"), namespace="catalog")),
    path(api_prefix, include((inventory_urls, "api"), namespace="inventory")),
    path("", include("social_django.urls", namespace="social")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
