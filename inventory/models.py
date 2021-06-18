""" This module stores the data model for Catalog Inventory
    The inventory is basically a collection of objects from the
    Automation Controller (Ansible Tower). The objects that we collect
    are
    1. Job Templates
    2. Workflows
    3. Inventory
    4. Survey Spec
"""

from django.db import models

from .basemodel import BaseModel


class TowerModel(BaseModel):
    """The common properties across Tower object"""

    source_created_at = models.DateTimeField()
    source_updated_at = models.DateTimeField()
    source_ref = models.CharField(max_length=32)

    class Meta:
        abstract = True


class ServiceInventory(TowerModel):
    """ServiceInventory models the Tower Inventory Object"""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    extra = models.JSONField()

    def __str__(self):
        return self.name


class OfferingKind(models.IntegerChoices):
    JOB_TEMPLATE = 0, "JobTemplate"
    WORKFLOW = 1, "Workflow"


class ServiceOffering(TowerModel):
    """Service offering object stores references to the Tower
    Job Templates and Workflows.
    """

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    service_inventory = models.ForeignKey(
        ServiceInventory, on_delete=models.SET_NULL, blank=True, null=True
    )
    survey_enabled = models.BooleanField(default=False)
    kind = models.IntegerField(
        default=OfferingKind.JOB_TEMPLATE, choices=OfferingKind.choices
    )
    extra = models.JSONField()

    def __str__(self):
        return self.name


class ServiceOfferingNode(TowerModel):
    """Service offeringNodes object stores relationship between different
    Workflow elements.
    """

    service_inventory = models.ForeignKey(
        ServiceInventory, on_delete=models.SET_NULL, blank=True, null=True
    )
    service_offering = models.ForeignKey(
        ServiceOffering, on_delete=models.SET_NULL, blank=True, null=True
    )
    root_service_offering = models.ForeignKey(
        ServiceOffering,
        related_name="root_service_offering",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    extra = models.JSONField()


class ServicePlan(TowerModel):
    """Service Plan object stores tower surveys and links it to a
    ServiceOffering
    """

    name = models.CharField(max_length=255, blank=True)
    service_offering = models.ForeignKey(
        ServiceOffering, on_delete=models.SET_NULL, blank=True, null=True
    )
    extra = models.JSONField()
    create_json_schema = models.JSONField()
    update_json_schema = models.JSONField(null=True)

    def __str__(self):
        return self.name
