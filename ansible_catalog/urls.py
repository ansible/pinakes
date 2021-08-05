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

from main.catalog.urls import router as catalog_router
from main.approval.urls import router as approval_router
from main.inventory.urls import router as inventory_router

router = routers.DefaultRouter()
router.registry.extend(catalog_router.registry)
router.registry.extend(approval_router.registry)
router.registry.extend(inventory_router.registry)

urlpatterns = [
    path(r"api/v1/", include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
