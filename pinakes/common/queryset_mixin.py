"""provides a common implementation of get_queryset method in viewset"""

from django.http import Http404

from pinakes.main.models import Tenant


class QuerySetMixin:
    """
    A Mixin class to be inherited by a customer ViewSet class
    """

    def get_queryset(self):
        """filter by current tenant and query_lookup_key, order by queryset_order_by"""

        parent_field_names = getattr(self, "parent_field_names", [])
        queryset_order_by = getattr(self, "queryset_order_by", None)
        serializer_class = self.get_serializer_class() or self.serializer_class

        # If this is swagger return back the empty qs
        if getattr(self, "swagger_fake_view", False):
            return serializer_class.Meta.model.objects.none()

        queryset = serializer_class.Meta.model.objects.filter(
            tenant=Tenant.current()
        )
        for parent_field_name in parent_field_names:
            parent_lookup_key = f"{parent_field_name}_id"
            if parent_lookup_key in self.kwargs:
                try:
                    queryset = queryset.filter(
                        **{parent_field_name: self.kwargs[parent_lookup_key]}
                    )
                except ValueError:
                    raise Http404
        if queryset_order_by is not None:
            queryset = queryset.order_by(queryset_order_by)
        return queryset
