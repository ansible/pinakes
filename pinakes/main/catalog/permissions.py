from typing import Any

from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework.request import Request

from pinakes.common.auth.keycloak_django.permissions import (
    KeycloakPolicy,
    BaseKeycloakPermission,
    check_wildcard_permission,
    check_object_permission,
    get_permitted_resources,
    KeycloakPoliciesMap,
)
from pinakes.main.catalog.models import (
    Portfolio,
    PortfolioItem,
    Order,
    ProgressMessage,
    ServicePlan,
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
            request,
        )

    def perform_check_object_permission(
        self, permission, request: Request, view: Any, obj: Any
    ) -> bool:
        if not isinstance(obj, Portfolio):
            return False
        return check_object_permission(
            obj,
            permission,
            request,
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
            request,
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
        return check_object_permission(
            obj,
            permission,
            request,
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
            request,
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
        "submit": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
        "cancel": KeycloakPolicy("update", KeycloakPolicy.Type.OBJECT),
    }

    def perform_check_object_permission(
        self,
        permission: str,
        request: Request,
        view: Any,
        obj: Any,
    ) -> bool:
        if check_wildcard_permission(
            obj.keycloak_type(),
            permission,
            request,
        ):
            return True
        return obj.user == request.user

    def perform_scope_queryset(
        self, permission: str, request: Request, view: Any, qs: models.QuerySet
    ) -> models.QuerySet:
        if check_wildcard_permission(
            Order.keycloak_type(),
            permission,
            request,
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
        obj: Any,
    ) -> bool:
        return self._check_order_permission(permission, request, obj.order)

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
            request,
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
            request,
        )


class ProgressMessagePermission(BaseKeycloakPermission):
    access_policies = {
        "list": KeycloakPolicy("read", KeycloakPolicy.Type.WILDCARD),
    }

    def perform_check_permission(
        self, permission: str, request: Request, view: Any
    ) -> bool:
        messageable_id = view.kwargs["messageable_id"]
        obj = get_object_or_404(view.messageable_model, pk=messageable_id)
        if obj.user == request.user:
            return True
        return check_wildcard_permission(
            ProgressMessage.keycloak_type(),
            permission,
            request,
        )


class ServicePlanPermission(BaseKeycloakPermission):

    portfolio_item_access_policies = {
        "list": KeycloakPolicy("read", KeycloakPolicy.Type.WILDCARD),
    }
    root_access_policies = {
        "retrieve": KeycloakPolicy("read", KeycloakPolicy.Type.WILDCARD),
        "partial_update": KeycloakPolicy(
            "update", KeycloakPolicy.Type.WILDCARD
        ),
        "reset": KeycloakPolicy("update", KeycloakPolicy.Type.WILDCARD),
    }

    def get_access_policies(
        self, request: Request, view: Any
    ) -> KeycloakPoliciesMap:
        if "portfolio_item_id" in view.kwargs:
            return self.portfolio_item_access_policies
        else:
            return self.root_access_policies

    def perform_check_permission(
        self, permission: str, request: Request, view: Any
    ) -> bool:
        portfolio_item_id = view.kwargs.get("portfolio_item_id")
        if portfolio_item_id is not None:
            portfolio_item = get_object_or_404(
                PortfolioItem, pk=portfolio_item_id
            )
        else:
            service_plan = get_object_or_404(ServicePlan, pk=view.kwargs["pk"])
            portfolio_item = service_plan.portfolio_item

        if PortfolioItemPermission().perform_check_object_permission(
            permission, request, view, portfolio_item
        ):
            return True
        return check_wildcard_permission(
            ServicePlan.keycloak_type(), permission, request
        )
