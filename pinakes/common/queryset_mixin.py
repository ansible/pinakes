"""provides a common implementation of get_queryset method in viewset"""

from django.http import Http404

from pinakes.main.models import Tenant
from pinakes.common.auth.keycloak_django.permissions import (
    get_permitted_resources,
)
from pinakes.common.auth.keycloak_django.clients import get_authz_client


class QuerySetMixin:
    """
    A Mixin class to be inherited by a customer ViewSet class
    """

    def get_queryset(self):
        """filter by current tenant and query_lookup_key, order by queryset_order_by"""

        parent_field_names = getattr(self, "parent_field_names", [])
        queryset_order_by = getattr(self, "queryset_order_by", None)
        serializer_class = self.get_serializer_class() or self.serializer_class
        queryset = serializer_class.Meta.model.objects.filter(
            tenant=Tenant.current()
        )
        result = self.get_keycloak_resource_ids()
        if result:
            if not result.is_wildcard:
                queryset = queryset.filter(pk__in=result.items)

        for parent_field_name in parent_field_names:
            parent_lookup_key = f"{parent_field_name}_id"
            if parent_lookup_key in self.kwargs:
                try:
                    queryset = queryset.filter(
                        **{parent_field_name: self.kwargs[parent_lookup_key]}
                    )
                except ValueError as ex:
                    raise Http404 from ex
        if queryset_order_by is not None:
            queryset = queryset.order_by(queryset_order_by)
        return queryset

    def get_keycloak_resource_ids(self):
        """Get the result set of allowed keycloak resources"""

        serializer_class = self.get_serializer_class() or self.serializer_class
        model_cls = serializer_class.Meta.model
        social = self.request.user.social_auth.get(provider="keycloak-oidc")
        client = get_authz_client(social.extra_data["access_token"])
        keycloak_type = getattr(model_cls, "KEYCLOAK_TYPE", None)
        # For models that don't have KEYCLOAK_TYPE ignore them
        if not keycloak_type:
            return None
        return get_permitted_resources(keycloak_type, "read", client)
