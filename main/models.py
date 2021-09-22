""" This module stores the base models needed for Catalog. """
from django.db import models
from django.db.utils import OperationalError
from django.db.models.functions import Length
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

models.CharField.register_lookup(Length)

class Tenant(models.Model):
    """Tenant"""

    external_tenant = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.external_tenant

    @classmethod
    def current(cls):
        """Return the first available tenant"""
        try:
            tenant, _ = cls.objects.get_or_create(external_tenant="default")
            return tenant
        except OperationalError:  # Table does not exist at the first migration
            return cls()


class BaseModel(models.Model):
    """Base Model"""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Source(models.Model):
    """Source"""

    name = models.CharField(max_length=255, unique=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SourceOwnedModel(BaseModel):
    """SourceOwnedModel"""

    source = models.ForeignKey(Source, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class UserOwnedModel(BaseModel):
    """User Owned Model"""

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    @property
    @extend_schema_field(OpenApiTypes.STR)
    def owner(self):
        """Use for serializer_class"""
        return self.user.username


class Image(models.Model):
    """ImageModel"""

    file = models.ImageField(blank=True, null=True)
    source_ref = models.CharField(max_length=32, default="")

    # delete image file from local storage
    def delete(self):
        self.file.storage.delete(self.file.name)
        super().delete()

    def __str__(self):
        return str(self.id)


class ImageableModel(BaseModel):
    """ImagableModel"""

    icon = models.ForeignKey(
        Image, blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        abstract = True
