"""PortfolioPermission Module"""
import json
import logging
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import DjangoModelPermissions
from pinakes.main.catalog.models import Portfolio

logger = logging.getLogger("catalog")


class PortfolioPermissions(DjangoModelPermissions):
    perms_map = {
        "list": ["%(app_label)s.view_%(model_name)s"],
        "retrieve": ["%(app_label)s.view_%(model_name)s"],
        "create": ["%(app_label)s.add_%(model_name)s"],
        "update": ["%(app_label)s.change_%(model_name)s"],
        "partial_update": ["%(app_label)s.change_%(model_name)s"],
        "destroy": ["%(app_label)s.delete_%(model_name)s"],
        # Custom actions
        # Icons
        "icon": ["%(app_label)s.change_%(model_name)s"],
        # Tags
        "tags": ["%(app_label)s.view_%(model_name)s"],
        "tag": ["%(app_label)s.change_%(model_name)s"],
        "untag": ["%(app_label)s.change_%(model_name)s"],
        # Sharing
        "share": ["%(app_label)s.change_%(model_name)s"],
        "unshare": ["%(app_label)s.change_%(model_name)s"],
        "share_info": ["%(app_label)s.change_%(model_name)s"],
        "copy": [
            "%(app_label)s.view_%(model_name)s",
            "%(app_label)s.add_%(model_name)s",
        ],
    }

    def get_required_object_permissions(self, action, model_cls):
        """Get the required permissions based on the  current action"""
        kwargs = {
            "app_label": model_cls._meta.app_label,
            "model_name": model_cls._meta.model_name,
        }
        if action not in self.perms_map:
            raise MethodNotAllowed(action)
        return [perm % kwargs for perm in self.perms_map[action]]

    def has_permission(self, request, view):
        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if getattr(view, "_ignore_model_permissions", False):
            return True

        if not request.user or (
            not request.user.is_authenticated and self.authenticated_users_only
        ):
            return False
        queryset = self._queryset(view)
        perms = self.get_required_permissions(view.action, queryset.model)
        request.user.get_all_permissions()

        if view.action == "create":
            return request.user.has_perm(perms[0])

        return True

    def has_object_permission(self, request, view, obj):
        """Check a single objects permission"""
        queryset = self._queryset(view)
        model_cls = queryset.model
        _clear_perm_cache(request.user)
        request.user.get_all_permissions(obj)

        perms = self.get_required_object_permissions(view.action, model_cls)
        return request.user.has_perm(perms[0], obj)


class PortfolioItemPermissions(DjangoModelPermissions):
    perms_map = {
        "list": ["%(app_label)s.view_%(model_name)s"],
        "retrieve": ["%(app_label)s.view_%(model_name)s"],
        "create": ["%(app_label)s.change_%(model_name)s"],
        "update": ["%(app_label)s.change_%(model_name)s"],
        "partial_update": ["%(app_label)s.change_%(model_name)s"],
        "destroy": ["%(app_label)s.change_%(model_name)s"],
        # Custom actions
        # Icons
        "icon": ["%(app_label)s.change_%(model_name)s"],
        # Tags
        "tags": ["%(app_label)s.view_%(model_name)s"],
        "tag": ["%(app_label)s.change_%(model_name)s"],
        "untag": ["%(app_label)s.change_%(model_name)s"],
        "copy": [
            "%(app_label)s.view_%(model_name)s",
            "%(app_label)s.change_%(model_name)s",
        ],
    }

    def get_required_object_permissions(self, action, model_cls):
        """Get the required permissions based on the  current action"""
        kwargs = {
            "app_label": model_cls._meta.app_label,
            "model_name": model_cls._meta.model_name,
        }
        if action not in self.perms_map:
            raise MethodNotAllowed(action)
        return [perm % kwargs for perm in self.perms_map[action]]

    def has_permission(self, request, view):
        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if getattr(view, "_ignore_model_permissions", False):
            return True

        if not request.user or (
            not request.user.is_authenticated and self.authenticated_users_only
        ):
            return False

        model_cls = Portfolio
        perms = self.get_required_permissions(view.action, model_cls)
        request.user.get_all_permissions()

        if view.action == "create":
            logger.info(request.data)
            if "portfolio" in request.data:
                obj = Portfolio.objects.get(pk=request.data["portfolio"])
                logger.info(obj)
                return request.user.has_perm(perms[0], obj)

        return True

    def has_object_permission(self, request, view, obj):
        """Check a single objects permission"""
        model_cls = Portfolio
        _clear_perm_cache(request.user)
        logger.info("Get single object permission")
        logger.info(obj.portfolio.name)
        kperms = request.user.get_all_permissions(obj.portfolio)
        logger.info(kperms)

        logger.info("Required object permission")
        perms = self.get_required_object_permissions(view.action, model_cls)
        logger.info(perms)

        return request.user.has_perm(perms[0], obj.portfolio)

class ServicePlanPermissions(DjangoModelPermissions):
    """ServicePlanPermission is controlled by the Portfolio Object"""
    perms_map = {
        "retrieve": ["%(app_label)s.view_%(model_name)s"],
        "reset": ["%(app_label)s.change_%(model_name)s"],
        "partial_update": ["%(app_label)s.change_%(model_name)s"],
    }

    def get_required_object_permissions(self, action, model_cls):
        """Get the required permissions based on the  current action"""
        kwargs = {
            "app_label": model_cls._meta.app_label,
            "model_name": model_cls._meta.model_name,
        }
        if action not in self.perms_map:
            raise MethodNotAllowed(action)
        return [perm % kwargs for perm in self.perms_map[action]]

    def has_permission(self, request, view):
        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if getattr(view, "_ignore_model_permissions", False):
            return True

        if not request.user or (
            not request.user.is_authenticated and self.authenticated_users_only
        ):
            return False

        return True

    def has_object_permission(self, request, view, obj):
        """Check a single objects permission"""
        model_cls = Portfolio
        portfolio = obj.portfolio_item.portfolio
        _clear_perm_cache(request.user)
        kperms =request.user.get_all_permissions(portfolio)
        logger.info("Service Plan")
        logger.info(kperms)

        perms = self.get_required_object_permissions(view.action, model_cls)
        logger.info("Required Service Plan")
        logger.info(perms)
        return request.user.has_perm(perms[0], portfolio)


def _clear_perm_cache(user):
    for attr in ("_perm_cache", "_user_perm_cache", "_group_perm_cache"):
        if hasattr(user, attr):
            delattr(user, attr)
