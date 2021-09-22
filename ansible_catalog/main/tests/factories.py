""" Factory for catalog objects """
import factory
from django.contrib.auth.models import User

from ansible_catalog.main.models import Tenant


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User"""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")


class TenantFactory(factory.django.DjangoModelFactory):
    """Tenant Factory"""

    class Meta:
        model = Tenant

    external_tenant = factory.Sequence(lambda n: f"external{n}")


def default_tenant():
    current = Tenant.current()
    if current is None:
        current = Tenant.objects.create(external_tenant="default")
    return current
