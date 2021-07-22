"""provides a common implementation of get_queryset method in viewset"""

from approval.basemodel import Tenant

class QuerySetMixin():
    """
    A Mixin class to be inherited by a customer ViewSet class
    """

    def get_queryset(self):
        """filter by current tenant and query_lookup_key, order by queryset_order_by"""

        parent_lookup_key = getattr(self, "parent_lookup_key", None)
        parent_field_name = getattr(self, "parent_field_name", None)
        queryset_order_by = getattr(self, "queryset_order_by", None)
        queryset = self.serializer_class.Meta.model.objects.filter(tenant=Tenant.current())
        if parent_lookup_key in self.kwargs:
            queryset = queryset.filter(**{parent_field_name: self.kwargs[parent_lookup_key]})
        if queryset_order_by is not None:
            queryset = queryset.order_by(queryset_order_by)
        return queryset
