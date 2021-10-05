""" This modules stores the definition of the Catalog model."""
import logging

from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import models
from django.db.models.functions import Length
from taggit.managers import TaggableManager

from ansible_catalog.main.models import (
    BaseModel,
    Image,
    ImageableModel,
    Tenant,
    UserOwnedModel,
)

models.CharField.register_lookup(Length)

logger = logging.getLogger("catalog")


class Portfolio(ImageableModel):
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

    def delete(self):
        if self.icon_id is not None:
            image = Image.objects.get(id=self.icon_id)
            image.delete()

        super().delete()

    @property
    def tag_resources(self):
        return list(self.tags.all())

    def __str__(self):
        return self.name


class PortfolioItem(ImageableModel):
    """Portfolio Item represent a Job Template or a Workflow."""

    favorite = models.BooleanField(default=False)
    description = models.TextField(blank=True, default="")
    orphan = models.BooleanField(default=False)
    state = models.CharField(max_length=64)
    service_offering_ref = models.CharField(max_length=64, null=True)
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

    def delete(self):
        if self.icon_id is not None:
            icon = Image.objects.get(id=self.icon_id)
            icon.delete()

        super().delete()

    @property
    def tag_resources(self):
        return list(self.tags.all())

    def __str__(self):
        return self.name


class ProgressMessage(BaseModel):
    """Progress Message Model"""

    class Level(models.TextChoices):
        """Available levels for ProgressMessage"""

        INFO = "Info"
        ERROR = "Error"
        WARNING = "Warning"
        DEBUG = "Debug"

    level = models.CharField(
        max_length=10,
        choices=Level.choices,
        default=Level.INFO,
        editable=False,
    )

    received_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True, default="")
    messageable_type = models.CharField(max_length=64, null=True)
    messageable_id = models.IntegerField(editable=False, null=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["tenant", "messageable_id", "messageable_type"]
            )
        ]

    def __str__(self):
        return self.message


class MessageableMixin:
    """MessageableModel"""

    def update_message(self, level, message):
        ProgressMessage.objects.create(
            level=level,
            messageable_type=self.__class__.__name__,
            messageable_id=self.id,
            message=message,
            tenant=self.tenant,
        )

    def mark_approval_pending(self, message=None):
        if self.state == self.__class__.State.PENDING:
            return

        self.__mark_item(
            message=message,
            completed_at=timezone.now(),
            state=self.__class__.State.PENDING,
        )

    def mark_ordered(self, message=None, **kwargs):
        if self.state == self.__class__.State.ORDERED:
            return

        self.__mark_item(
            message=message,
            order_request_sent_at=timezone.now(),
            state=self.__class__.State.ORDERED,
            **kwargs,
        )

    def mark_failed(self, message=None, **kwargs):
        if self.state == self.__class__.State.FAILED:
            return

        self.__mark_item(
            message=message,
            level=ProgressMessage.Level.ERROR,
            completed_at=timezone.now(),
            state=self.__class__.State.FAILED,
            **kwargs,
        )

    def mark_completed(self, message=None, **kwargs):
        if self.state == self.__class__.State.COMPLETED:
            return

        self.__mark_item(
            message=message,
            completed_at=timezone.now(),
            state=self.__class__.State.COMPLETED,
            **kwargs,
        )

    def mark_canceled(self, message=None):
        if self.state == self.__class__.State.CANCELED:
            return

        self.__mark_item(
            message=message,
            completed_at=timezone.now(),
            state=self.__class__.State.CANCELED,
        )

    def __mark_item(
        self, message, level=ProgressMessage.Level.INFO, **options
    ):
        if message is not None:
            self.update_message(level, message)

        self.__class__.objects.filter(id=self.id).update(**options)
        self.refresh_from_db()

        logger.info(
            "Updated %s: %d with state: %s",
            self.__class__.__name__,
            self.id,
            options["state"],
        )


class Order(UserOwnedModel, MessageableMixin):
    """Order object to wrap order items."""

    class State(models.TextChoices):
        """Available states for Order"""

        PENDING = "Pending"  # Approval
        APPROVED = "Approved"
        CANCELED = "Canceled"
        COMPLETED = "Completed"
        CREATED = "Created"
        DENIED = "Denied"
        FAILED = "Failed"
        ORDERED = "Ordered"

    state = models.CharField(
        max_length=10,
        choices=State.choices,
        default=State.CREATED,
        editable=False,
    )
    order_request_sent_at = models.DateTimeField(editable=False, null=True)
    completed_at = models.DateTimeField(editable=False, null=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "user"])]

    @property
    def order_items(self):
        return OrderItem.objects.filter(order_id=self.id)

    @property
    def product(self):
        # TODO: return the true product when order process introduced
        return OrderItem.objects.filter(order_id=self.id).first()

    def __str__(self):
        return str(self.id)


class OrderItemManager(models.Manager):
    """Override default manager with create method"""

    def create(self, *args, **kwargs):
        from ansible_catalog.main.catalog.services.sanitize_parameters import (
            SanitizeParameters,
        )

        order_item = super(OrderItemManager, self).create(*args, **kwargs)

        sanitized_parameters = (
            SanitizeParameters(order_item).process().sanitized_parameters
        )
        if order_item.service_parameters == sanitized_parameters:
            return order_item

        order_item.service_parameters_raw = order_item.service_parameters
        order_item.service_parameters = sanitized_parameters

        return order_item


class OrderItem(UserOwnedModel, MessageableMixin):
    """Order Item Model"""

    class State(models.TextChoices):
        """Available states for Order Item"""

        PENDING = "Pending"  # Approval
        APPROVED = "Approved"
        CANCELED = "Canceled"
        COMPLETED = "Completed"
        CREATED = "Created"
        DENIED = "Denied"
        FAILED = "Failed"
        ORDERED = "Ordered"

    FINISHED_STATES = [
        State.COMPLETED,
        State.CANCELED,
        State.FAILED,
        State.DENIED,
    ]

    objects = OrderItemManager()
    name = models.CharField(max_length=64)
    state = models.CharField(
        max_length=10,
        choices=State.choices,
        default=State.CREATED,
        editable=False,
    )
    order_request_sent_at = models.DateTimeField(editable=False, null=True)
    completed_at = models.DateTimeField(editable=False, null=True)
    count = models.SmallIntegerField(editable=False, default=0)
    inventory_task_ref = models.CharField(max_length=64, null=True)
    service_plan_ref = models.CharField(max_length=64, null=True)
    service_instance_ref = models.CharField(max_length=64, null=True)
    service_parameters = models.JSONField(blank=True, null=True)
    service_parameters_raw = models.JSONField(blank=True, null=True)
    provider_control_parameters = models.JSONField(blank=True, null=True)
    context = models.JSONField(blank=True, null=True)
    artifacts = models.JSONField(blank=True, null=True)
    external_url = models.URLField(blank=True)

    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    portfolio_item = models.ForeignKey(PortfolioItem, on_delete=models.CASCADE)

    class Meta:
        indexes = [models.Index(fields=["tenant", "user"])]
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

    def __str__(self):
        return self.name


class ApprovalRequestManager(models.Manager):
    """Override default manager with create method"""

    def create(self, *args, **kwargs):
        approval_request = super(ApprovalRequestManager, self).create(
            *args, **kwargs
        )

        approval_request_ref = kwargs.pop("approval_request_ref", None)
        message = _(
            "Created Approval Request ref: {}. Catalog approval request id: {}"
        ).format(approval_request_ref, approval_request.id)
        approval_request.order.update_message(
            ProgressMessage.Level.INFO, message
        )

        return approval_request


class ApprovalRequest(BaseModel):
    """Approval Request Model"""

    class State(models.TextChoices):
        """Available states for approval request"""

        UNDECIDED = "Undecided"
        APPROVED = "Approved"
        CANCELED = "Canceled"
        DENIED = "Denied"
        FAILED = "Failed"

    objects = ApprovalRequestManager()
    approval_request_ref = models.CharField(max_length=64, default="")
    reason = models.TextField(blank=True, default="")
    request_completed_at = models.DateTimeField(editable=False, null=True)
    state = models.CharField(
        max_length=10,
        choices=State.choices,
        default=State.UNDECIDED,
        editable=False,
    )

    order = models.OneToOneField(Order, on_delete=models.CASCADE)

    class Meta:
        indexes = [models.Index(fields=["tenant", "order"])]

    def __str__(self):
        return str(self.id)


class CatalogServicePlan(BaseModel):
    """Catalog Service Plan Model"""

    name = models.CharField(max_length=255, blank=True, null=True)
    base_schema = models.JSONField(blank=True, null=True)
    modified_schema = models.JSONField(blank=True, null=True)
    create_json_schema = models.JSONField(blank=True, null=True)
    service_plan_ref = models.CharField(max_length=64, null=True)
    service_offering_ref = models.CharField(max_length=64, null=True)
    modified = models.BooleanField(default=False)
    imported = models.BooleanField(default=False)

    portfolio_item = models.ForeignKey(PortfolioItem, on_delete=models.CASCADE)

    class Meta:
        indexes = [models.Index(fields=["tenant", "portfolio_item"])]

    def __str__(self):
        return self.name
