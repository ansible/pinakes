""" This module stores the base models needed for Catalog. """
from django.db import models
from django.db.utils import OperationalError
from django.db.models.functions import Length
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

models.CharField.register_lookup(Length)


class Tenant(models.Model):
    """Tenant"""

    external_tenant = models.CharField(
        max_length=32, unique=True, help_text="User's account number"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The time at which the object was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="The time at which the object was last updated",
    )

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

    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The time at which the object was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="The time at which the object was last updated",
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        help_text="ID of the tenant the object belongs to",
    )

    class Meta:
        abstract = True


class Source(models.Model):
    """Source"""

    class State(models.TextChoices):
        """states for Source"""

        DONE = "Done"
        INPROGRESS = "InProgress"
        FAILED = "Failed"
        UNKNOWN = "Unknown"

    name = models.CharField(
        max_length=255, unique=True, help_text="Name of the source"
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        help_text="ID of the tenant the object belongs to",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="The time at which the object was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="The time at which the object was last updated",
    )
    refresh_state = models.CharField(
        max_length=32,
        choices=State.choices,
        default=State.UNKNOWN,
        editable=False,
        help_text="State of current refresh",
    )
    refresh_started_at = models.DateTimeField(
        editable=False,
        null=True,
        help_text="The time at which the source refresh is started",
    )
    refresh_finished_at = models.DateTimeField(
        editable=False,
        null=True,
        help_text="The time at which the source refresh is finished",
    )
    last_successful_refresh_at = models.DateTimeField(
        editable=False,
        null=True,
        help_text="The time at which the latest source refresh was succeeded",
    )
    last_refresh_message = models.TextField(
        blank=True,
        default="",
        help_text="The message for the last source refresh",
    )
    last_refresh_task_ref = models.CharField(
        max_length=64, null=True, help_text="The last refresh task id"
    )
    availability_status = models.TextField(
        blank=True,
        default="unavailable",
        help_text="The status for the source availability status",
    )
    last_available_at = models.DateTimeField(
        editable=False,
        null=True,
        help_text="The time at which the source was available",
    )
    last_checked_at = models.DateTimeField(
        editable=False,
        null=True,
        help_text="The time at which the source was checked availability",
    )
    availability_message = models.TextField(
        blank=True,
        default="Unavailable",
        help_text="The message about the source availability",
    )
    info = models.JSONField(
        blank=True,
        null=True,
        help_text="The information about the source",
    )

    def __str__(self):
        return self.name


class SourceOwnedModel(BaseModel):
    """SourceOwnedModel"""

    source = models.ForeignKey(
        Source,
        on_delete=models.CASCADE,
        help_text="ID of the source that this object belongs to",
    )

    class Meta:
        abstract = True


class UserOwnedModel(BaseModel):
    """User Owned Model"""

    user = models.ForeignKey(
        get_user_model(),
        null=True,
        on_delete=models.CASCADE,
        help_text="ID of the user who created this object",
    )

    class Meta:
        abstract = True

    @property
    @extend_schema_field(OpenApiTypes.STR)
    def owner(self):
        """Use for serializer_class"""
        return f"{self.user.first_name} {self.user.last_name}"


class Image(models.Model):
    """ImageModel"""

    file = models.ImageField(blank=True, null=True, help_text="The image file")
    source_ref = models.CharField(max_length=32, default="")

    # delete image file from local storage
    def delete(self):
        self.file.storage.delete(self.file.name)
        super().delete()

    def __str__(self):
        return str(self.id)


class ImageableModel(models.Model):
    """ImagableModel"""

    icon = models.ForeignKey(
        Image,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text="ID of the icon image associated with this object",
    )

    class Meta:
        abstract = True
