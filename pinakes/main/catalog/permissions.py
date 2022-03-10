from typing import Any, Union

from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework.request import Request

from pinakes.common.auth.keycloak_django.clients import (
    get_authz_client,
)
from pinakes.common.auth.keycloak_django.permissions import (
    KeycloakPolicy,
    BaseKeycloakPermission,
    check_wildcard_permission,
    check_resource_permission,
    get_permitted_resources,
)
from pinakes.main.catalog.models import (
    Portfolio,
    PortfolioItem,
    Order,
    OrderItem,
)


class PortfolioPermission(BaseKeycloakPermission):
    access_policies = {
        "list": KeycloakPolicy("read", KeycloakPolicy.Type.QUERYSET),
        "retrieve": KeycloakPolicy("read", KeycloakPolicy.Type.OBJECT),
        "create": KeycloakPolicy("create", KeycloakPolicy.Type.WILDCARD),
        "update": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "partial_update": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "destroy": KeycloakPolicy("delete", KeycloakPolicy.Type.OBJECT),
        # Custom actions
        # Icons
        "icon": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        # Tags
        "tags": KeycloakPolicy("read", KeycloakPolicy.Type.OBJECT),
        "tag": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "untag": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        # Sharing
        "share": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "unshare": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "share_info": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        # Copy
        "copy": [
            KeycloakPolicy("create", KeycloakPolicy.Type.WILDCARD),
            KeycloakPolicy("read", KeycloakPolicy.Type.OBJECT),
        ],
    }

    def perform_check_permission(
        self, permission: str, request: Request, view: Any
    ) -> bool:
        return check_wildcard_permission(
            Portfolio.keycloak_type(),
            permission,
            get_authz_client(request.keycloak_user.access_token),
        )

    def perform_check_object_permission(
        self, permission, request: Request, view: Any, obj: Any
    ) -> bool:
        if not isinstance(obj, Portfolio):
            return False
        return check_resource_permission(
            obj.keycloak_type(),
            obj.keycloak_name(),
            permission,
            get_authz_client(request.keycloak_user.access_token),
        )

    def perform_scope_queryset(
        self,
        permission: str,
        request: Request,
        view: Any,
        qs: models.QuerySet,
    ) -> models.QuerySet:
        resources = get_permitted_resources(
            Portfolio.keycloak_type(),
            permission,
            get_authz_client(request.keycloak_user.access_token),
        )
        if resources.is_wildcard:
            return qs
        else:
            return qs.filter(pk__in=resources.items)


class PortfolioItemPermission(BaseKeycloakPermission):
    access_policies = {
        "retrieve": KeycloakPolicy("read", KeycloakPolicy.Type.OBJECT),
        "create": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "update": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "partial_update": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "destroy": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        # Tags
        "tags": KeycloakPolicy("read", KeycloakPolicy.Type.OBJECT),
        "tag": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "untag": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        # Custom actions
        "icon": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "copy": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "next_name": KeycloakPolicy("read", KeycloakPolicy.Type.OBJECT),
    }

    def get_access_policies(self, request: Request, view: Any):
        if "portfolio_id" in view.kwargs:
            policy_type = KeycloakPolicy.Type.OBJECT
        else:
            policy_type = KeycloakPolicy.Type.QUERYSET
        return {
            **self.access_policies,
            "list": KeycloakPolicy("read", policy_type),
        }

    def perform_check_object_permission(
        self,
        permission: str,
        request: Request,
        view: Any,
        obj: Any,
    ) -> bool:
        if isinstance(obj, PortfolioItem):
            obj = obj.portfolio
        elif not isinstance(obj, Portfolio):
            return False
        return check_resource_permission(
            obj.keycloak_type(),
            obj.keycloak_name(),
            permission,
            get_authz_client(request.keycloak_user.access_token),
        )

    def perform_scope_queryset(
        self,
        permission: str,
        request: Request,
        view: Any,
        qs: models.QuerySet,
    ) -> models.QuerySet:
        resources = get_permitted_resources(
            Portfolio.keycloak_type(),
            permission,
            get_authz_client(request.keycloak_user.access_token),
        )
        if resources.is_wildcard:
            return qs
        else:
            return qs.filter(portfolio__in=resources.items)


class OrderPermission(BaseKeycloakPermission):
    access_policies = {
        "list": KeycloakPolicy("read", KeycloakPolicy.Type.QUERYSET),
        "create": KeycloakPolicy("create", KeycloakPolicy.Type.WILDCARD),
        "retrieve": KeycloakPolicy("read", KeycloakPolicy.Type.OBJECT),
        "destroy": KeycloakPolicy("delete", KeycloakPolicy.Type.OBJECT),
        # Custom actions
        # TODO(cutwater): Define policies for `submit` and `cancel` actions.
        "submit": KeycloakPolicy("order", KeycloakPolicy.Type.OBJECT),
        "cancel": KeycloakPolicy("order", KeycloakPolicy.Type.OBJECT),
    }

    def perform_check_permission(
        self, permission: str, request: Request, view: Any
    ) -> bool:
        return check_wildcard_permission(
            Order.keycloak_type(),
            permission,
            get_authz_client(request.keycloak_user.access_token),
        )

    def perform_check_object_permission(
        self,
        permission: str,
        request: Request,
        view: Any,
        obj: Order,
    ) -> bool:
        if check_wildcard_permission(
            obj.keycloak_type(),
            permission,
            get_authz_client(request.keycloak_user.access_token),
        ):
            return True
        return obj.user == request.user

    def perform_scope_queryset(
        self, permission: str, request: Request, view: Any, qs: models.QuerySet
    ) -> models.QuerySet:
        if check_wildcard_permission(
            Order.keycloak_type(),
            permission,
            get_authz_client(request.keycloak_user.access_token),
        ):
            return qs
        return qs.filter(user=request.user)


class OrderItemPermission(BaseKeycloakPermission):
    access_policies = {
        "list": KeycloakPolicy("read", KeycloakPolicy.Type.QUERYSET),
        "retrieve": KeycloakPolicy("read", KeycloakPolicy.Type.OBJECT),
        "create": KeycloakPolicy("update", KeycloakPolicy.Type.WILDCARD),
        "update": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "partial_update": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "destroy": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
    }

    def perform_check_permission(
        self, permission: str, request: Request, view: Any
    ) -> bool:
        order_id = view.kwargs.get("order_id")
        if order_id is None:
            return False
        order = get_object_or_404(Order, pk=order_id)
        return self._check_order_permission(permission, request, order)

    def perform_check_object_permission(
        self,
        permission: str,
        request: Request,
        view: Any,
        obj: OrderItem,
    ) -> bool:
        if check_wildcard_permission(
            obj.order.keycloak_type(),
            permission,
            get_authz_client(request.keycloak_user.access_token),
        ):
            return True
        # NOTE(cutwater): OrderItem and Order models both have FK to user.
        return obj.user == request.user

    def perform_scope_queryset(
        self,
        permission: str,
        request: Request,
        view: Any,
        qs: models.QuerySet,
    ) -> models.QuerySet:
        if check_wildcard_permission(
            Order.keycloak_type(),
            permission,
            get_authz_client(request.keycloak_user.access_token),
        ):
            return qs
        # NOTE(cutwater): OrderItem and Order models both have FK to user.
        return qs.filter(order__user=request.user)

    def _check_order_permission(
        self, permission: str, request: Request, order: Order
    ) -> bool:
        if order.user == request.user:
            return True
        return check_wildcard_permission(
            order.keycloak_type(),
            permission,
            get_authz_client(request.keycloak_user.access_token),
        )
