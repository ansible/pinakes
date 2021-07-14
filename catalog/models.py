""" This modules stores the definition of the Catalog model."""

from django.db import models
from django.db.models.functions import Length
from django.contrib.auth.models import User
from taggit.managers import TaggableManager

from .basemodel import BaseModel

models.CharField.register_lookup(Length)


class Portfolio(BaseModel):
    """Portfolio object to wrap products."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    enabled = models.BooleanField(default=False)
    owner = models.CharField(max_length=255)

    tags = TaggableManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_name_empty",
                check=models.Q(name__length__gt=0),
            ),
            models.UniqueConstraint(
                name="%(app_label)s_%(class)s_name_unique",
                fields=["name", "tenant"],
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class PortfolioItem(BaseModel):
    """Portfolio Item represent a Job Template or a Workflow."""

    favorite = models.BooleanField(default=False)
    description = models.TextField(blank=True, default="")
    orphan = models.BooleanField(default=False)
    state = models.CharField(max_length=64)
    service_offering_ref = models.CharField(max_length=64)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    service_offering_source_ref = models.CharField(
        max_length=64, blank=True, default=""
    )
    name = models.CharField(max_length=64)
    long_description = models.TextField(blank=True, default="")
    distributor = models.CharField(max_length=64)
    documentation_url = models.URLField(blank=True)
    support_url = models.URLField(blank=True)

    tags = TaggableManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_name_empty",
                check=models.Q(name__length__gt=0),
            ),
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_service_offering_empty",
                check=models.Q(service_offering_ref__length__gt=0),
            ),
            models.UniqueConstraint(
                name="%(app_label)s_%(class)s_name_unique",
                fields=["name", "tenant", "portfolio"],
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Order(BaseModel):
    """Order object to wrap order items."""

    class State(models.TextChoices):
        """Available states for Order"""
        PENDING = 'Pending' # Approval
        APPROVED = 'Approved'
        CANCELED = 'Canceled'
        COMPLETED = 'Completed'
        CREATED = 'Created'
        DENIED = 'Denied'
        FAILED = 'Failed'
        ORDERED = 'Ordered'

    state = models.CharField(
        max_length=10,
        choices=State.choices,
        default=State.CREATED,
        editable=False)
    order_request_sent_at = models.DateTimeField(editable=False, null=True)
    completed_at = models.DateTimeField(editable=False, null=True)
    owner = models.CharField(max_length=255, default="")
    user = models.ForeignKey(User, default=None, on_delete=models.CASCADE)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.id


class OrderItem(BaseModel):
    """Order Item Model"""

    class State(models.TextChoices):
        """Available states for Order Item"""
        PENDING = 'Pending' # Approval
        APPROVED = 'Approved'
        CANCELED = 'Canceled'
        COMPLETED = 'Completed'
        CREATED = 'Created'
        DENIED = 'Denied'
        FAILED = 'Failed'
        ORDERED = 'Ordered'

    name = models.CharField(max_length=64)
    state = models.CharField(
        max_length=10,
        choices=State.choices,
        default=State.CREATED,
        editable=False)
    order_request_sent_at = models.DateTimeField(editable=False, null=True)
    completed_at = models.DateTimeField(editable=False, null=True)
    owner = models.CharField(max_length=255, default="")
    count = models.SmallIntegerField(editable=False, default=0)
    inventory_task_ref = models.CharField(max_length=64, default="")
    service_plan_ref = models.CharField(max_length=64, default="")
    service_instance_ref = models.CharField(max_length=64, default="")
    service_parameters = models.JSONField(blank=True, null=True)
    service_parameters_raw = models.JSONField(blank=True, null=True)
    provider_control_parameters = models.JSONField(blank=True, null=True)
    context = models.JSONField(blank=True, null=True)
    artifacts = models.JSONField(blank=True, null=True)
    external_url = models.URLField(blank=True)

    user = models.ForeignKey(User, default=None, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    portfolio_item = models.ForeignKey(PortfolioItem, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_name_empty",
                check=models.Q(name__length__gt=0),
            ),
            models.UniqueConstraint(
                name="%(app_label)s_%(class)s_name_unique",
                fields=["name", "tenant", "order", "portfolio_item"],
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
