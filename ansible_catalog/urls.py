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


def __filter_by_view(pattern):
    name = pattern.name
    if name in urls_views:
        if urls_views[name] == None:
            return False
        pattern.callback = urls_views[name]
    return True


router = routers.DefaultRouter()
router.registry.extend(catalog_router.registry)
router.registry.extend(approval_router.registry)
router.registry.extend(inventory_router.registry)

api_urls = router.urls
urls_views = {**catalog_views, **approval_views, **inventory_views}
api_urls = [p for p in api_urls if __filter_by_view(p)]

API_PATH_PREFIX = settings.CATALOG_API_PATH_PREFIX.strip("/")
API_VER = "v1"

api_urls = [
    path(f"{API_PATH_PREFIX}/{API_VER}/", include(api_urls)),
]

urlpatterns = [
    path(
        f"{API_PATH_PREFIX}/{API_VER}/schema/openapi.json",
        SpectacularJSONAPIView.as_view(),
        name="schema",
    ),
    path(
        f"{API_PATH_PREFIX}/{API_VER}/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        f"{API_PATH_PREFIX}/{API_VER}/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("", include((api_urls, "api"), "catalog")),
    path("", include("social_django.urls", namespace="social")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
