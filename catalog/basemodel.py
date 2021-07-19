""" This module stores the base models needed for Catalog. """
from django.db import models
from django.db.utils import OperationalError
from django.contrib.auth.models import User


class Tenant(models.Model):
    """Tenant"""

    external_tenant = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def current(cls):
        """ Return the first available tenant """
        try:
            tenant, _ = cls.objects.get_or_create(external_tenant="default")
            return tenant
        except OperationalError: # Table does not exist at the first migration
            return cls()


    def __str__(self):
        return self.external_tenant


class BaseModel(models.Model):
    """Base Model"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        abstract = True

class UserOwnedModel(BaseModel):
    """User Owned Model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    @property
    def owner(self):
        " Use for serializer_class "
        return self.user.username
