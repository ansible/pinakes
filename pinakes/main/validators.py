"""
Customized rest_framework validators
"""
from rest_framework.serializers import PrimaryKeyRelatedField
from rest_framework.validators import UniqueTogetherValidator
from pinakes.main.models import Tenant


class UniqueWithinTenantValidator(UniqueTogetherValidator):
    """Validate uniquesness on joint columns including Tenant"""

    def __call__(self, attrs, serializer):
        tenant_attr = False
        if "tenant" not in attrs:
            attrs["tenant"] = Tenant.current()
            tenant_attr = True

        tenant_field = False
        if "tenant" not in serializer.fields:
            serializer.fields["tenant"] = PrimaryKeyRelatedField(
                queryset=Tenant.objects.all()
            )
            tenant_field = True

        super().__call__(attrs, serializer)

        if tenant_attr:
            del attrs["tenant"]

        if tenant_field:
            del serializer.fields["tenant"]
