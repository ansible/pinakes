""" Default views for Catalog."""
from rest_framework import viewsets
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from .basemodel import Tenant
from .models import Portfolio
from .models import PortfolioItem
from .serializers import TenantSerializer
from .serializers import PortfolioSerializer
from .serializers import PortfolioItemSerializer

# Create your views here.


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for listing and creating tenants."""

    queryset = Tenant.objects.all().order_by("id")
    serializer_class = TenantSerializer


class PortfolioViewSet(viewsets.ModelViewSet):
    """API endpoint for listing and creating portfolios."""

    queryset = Portfolio.objects.all().order_by("created_at")
    http_method_names = ["get", "post", "head", "patch", "delete"]

    def get_serializer_class(self):
        if self.action == "portfolio_items":
            return PortfolioItemSerializer
        else:
            return PortfolioSerializer

    @action(detail=True, url_name="portfolio_items")
    def portfolio_items(self, request, pk=None):
        portfolio = self.get_object()
        if request.method == "GET":
            portfolio_items = PortfolioItem.objects.filter(
                portfolio=portfolio
            ).order_by("created_at")
            page = self.paginate_queryset(portfolio_items)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(portfolio_items, many=True)
            return Response(serializer.data)


class PortfolioItemViewSet(viewsets.ModelViewSet):
    """API endpoint for listing and creating portfolio items."""

    queryset = PortfolioItem.objects.all()
    serializer_class = PortfolioItemSerializer
    http_method_names = ["get", "post", "head", "patch", "delete"]
