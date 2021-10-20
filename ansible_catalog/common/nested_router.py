"""Default nested router with a patched parent path variable name"""
from rest_framework_extensions import utils


def parent_pk_kwarg_name(value):
    """more meaningful parent path variable name and compatible with drf-spectacular"""
    return f"{value}_id"


utils.compose_parent_pk_kwarg_name = parent_pk_kwarg_name


# Do NOT move the following from to top of the file
from rest_framework_extensions.routers import NestedRouterMixin
from rest_framework.routers import DefaultRouter


class NestedDefaultRouter(NestedRouterMixin, DefaultRouter):
    pass
