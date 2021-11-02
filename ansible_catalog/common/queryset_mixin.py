"""provides a common implementation of get_queryset method in viewset"""

from ansible_catalog.main.models import Tenant


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
        for parent_field_name in parent_field_names:
            parent_lookup_key = f"{parent_field_name}_id"
            if parent_lookup_key in self.kwargs:
                queryset = queryset.filter(
                    **{parent_field_name: self.kwargs[parent_lookup_key]}
                )
        if queryset_order_by is not None:
            queryset = queryset.order_by(queryset_order_by)
        return queryset
