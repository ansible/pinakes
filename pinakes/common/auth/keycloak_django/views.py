from __future__ import annotations

from typing import Callable

from django.db.models import QuerySet
from rest_framework.request import Request
from rest_framework.views import APIView


ScopeQuerysetFn = Callable[[Request, APIView, QuerySet], QuerySet]


class PermissionQuerySetMixin:
    def get_queryset(self) -> QuerySet:
        qs = super().get_queryset()
        swagger_view = getattr(self, "swagger_fake_view", False)
        if swagger_view:
            return qs
        for permission in self.get_permissions():
            scope_queryset_fn: ScopeQuerysetFn = getattr(
                permission, "scope_queryset", None
            )
            if scope_queryset_fn:
                qs = scope_queryset_fn(self.request, self, qs)
        return qs
