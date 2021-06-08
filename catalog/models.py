""" This modules stores the definition of the Catalog model."""

from django.db import models
from django.db.models.functions import Length

from .basemodel import BaseModel

models.CharField.register_lookup(Length)


class Portfolio(BaseModel):
    """Portfolio object to wrap products."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    enabled = models.BooleanField(default=False)
    owner = models.CharField(max_length=255)

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
