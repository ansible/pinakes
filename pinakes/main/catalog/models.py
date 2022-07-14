"""This modules stores the definition of the Catalog model."""
import logging

from django.utils.translation import gettext_noop
from django.utils import timezone
from django.db import models
from django.db.models.functions import Length
from taggit.managers import TaggableManager

from pinakes.common.auth.keycloak_django import (
    AbstractKeycloakResource,
)
from pinakes.common.auth.keycloak_django.models import KeycloakMixin
from pinakes.main.models import (
    BaseModel,
    Image,
    ImageableModel,
    UserOwnedModel,
)

models.CharField.register_lookup(Length)

logger = logging.getLogger("catalog")


class Portfolio(AbstractKeycloakResource, ImageableModel, UserOwnedModel):
    """Portfolio object to wrap products."""

    KEYCLOAK_TYPE = "catalog:portfolio"
    KEYCLOAK_ACTIONS = ["read", "update", "delete", "order"]

    name = models.CharField(max_length=255, help_text="Portfolio name")
    description = models.TextField(
        blank=True, default="", help_text="Describe the portfolio in details"
    )
    enabled = models.BooleanField(
        default=False, help_text="Whether or not this portfolio is enabled"
    )
    share_count = models.IntegerField(
        default=0,
        help_text="The number of different groups sharing this portfolio",
    )

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

    @property
    def metadata(self):
        return {"statistics": self._statistics_metadata()}

    def _statistics_metadata(self):
        portfolio_item_number = PortfolioItem.objects.filter(
            portfolio=self
        ).count()

        return {
            "approval_processes": len(self.tag_resources),
            "portfolio_items": portfolio_item_number,
            "shared_groups": self.share_count,
        }

    def __str__(self):
        return self.name


class PortfolioItem(KeycloakMixin, ImageableModel, UserOwnedModel):
    """Portfolio Item represent a Job Template or a Workflow."""

    KEYCLOAK_TYPE = "catalog:portfolio"
    MAX_PORTFOLIO_ITEM_LENGTH = 512

    favorite = models.BooleanField(
        default=False, help_text="Definition of a favorite portfolio item"
    )
    description = models.TextField(
        blank=True, default="", help_text="Description of the portfolio item"
    )
    orphan = models.BooleanField(
        default=False,
        help_text="Boolean if an associated service offering no longer exists",
    )
    state = models.CharField(
        max_length=64, help_text="The current state of the portfolio item"
    )
    service_offering_ref = models.CharField(
        max_length=64,
        null=True,
        help_text="The service offering this portfolio item was created from",
    )
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        help_text="ID of the parent portfolio",
    )
    service_offering_source_ref = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="The source reference this portfolio item was created from",
    )
    name = models.CharField(
        max_length=MAX_PORTFOLIO_ITEM_LENGTH,
        help_text="Name of the portfolio item",
    )
    long_description = models.TextField(
        blank=True,
        default="",
        help_text="The longer description of the portfolio item",
    )
    distributor = models.CharField(
        max_length=64,
        help_text="The name of the provider for the portfolio item",
    )
    documentation_url = models.URLField(
        blank=True, help_text="The URL for documentation of the portfolio item"
    )
    support_url = models.URLField(
        blank=True,
        help_text="The URL for finding support for the portfolio item",
    )

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
        ]

    def delete(self):
        if self.icon_id is not None:
            icon = Image.objects.get(id=self.icon_id)
            icon.delete()

        super().delete()

    @property
    def tag_resources(self):
        return list(self.tags.all())

    @property
    def metadata(self):
        return {"statistics": self._statistics_metadata()}

    def _statistics_metadata(self):
        return {
            "approval_processes": len(self.tag_resources),
        }

    def __str__(self):
        return self.name


class ProgressMessage(KeycloakMixin, BaseModel):
    """Progress Message Model"""

    KEYCLOAK_TYPE = "catalog:progress_message"

    class Level(models.TextChoices):
        """Available levels for ProgressMessage"""

        INFO = gettext_noop("Info")
        ERROR = gettext_noop("Error")
        WARNING = gettext_noop("Warning")
        DEBUG = gettext_noop("Debug")

    level = models.CharField(
        max_length=10,
        choices=Level.choices,
        default=Level.INFO,
        editable=False,
        help_text="One of the predefined levels",
    )

    received_at = models.DateTimeField(
        auto_now_add=True, help_text="Message received at"
    )
    message = models.TextField(
        blank=True, default="", help_text="The message content"
    )
    messageable_type = models.CharField(
        max_length=64,
        editable=False,
        help_text="Identify order or order item that this message belongs to",
    )
    messageable_id = models.IntegerField(
        editable=False,
        help_text="ID of the order or order item",
    )

    message_params = models.JSONField(
        null=True,
        help_text="Stores message parameters used by localization",
    )

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

    def update_message(self, level, message, params=None):
        ProgressMessage.objects.create(
            level=level,
            messageable_type=self.__class__.__name__,
            messageable_id=self.id,
            message=message,
            message_params=params,
            tenant=self.tenant,
        )

    def mark_approval_pending(self, message=None, params=None):
        if self.state == self.__class__.State.PENDING:
            return

        self._mark_item(
            message=message,
            params=params,
            completed_at=timezone.now(),
            state=self.__class__.State.PENDING,
        )

    def mark_ordered(self, message=None, params=None, **kwargs):
        if self.state == self.__class__.State.ORDERED:
            return

        self._mark_item(
            message=message,
            params=params,
            order_request_sent_at=timezone.now(),
            state=self.__class__.State.ORDERED,
            **kwargs,
        )

    def mark_failed(self, message=None, params=None, **kwargs):
        if self.state == self.__class__.State.FAILED:
            return

        self._mark_item(
            message=message,
            params=params,
            level=ProgressMessage.Level.ERROR,
            completed_at=timezone.now(),
            state=self.__class__.State.FAILED,
            **kwargs,
        )

    def mark_completed(self, message=None, params=None, **kwargs):
        if self.state == self.__class__.State.COMPLETED:
            return

        self._mark_item(
            message=message,
            params=params,
            completed_at=timezone.now(),
            state=self.__class__.State.COMPLETED,
            **kwargs,
        )

    def mark_canceled(self, message=None, params=None):
        if self.state == self.__class__.State.CANCELED:
            return

        self._mark_item(
            message=message,
            params=params,
            completed_at=timezone.now(),
            state=self.__class__.State.CANCELED,
        )

    def _mark_item(
        self, message, level=ProgressMessage.Level.INFO, params=None, **options
    ):
        if message is not None:
            self.update_message(level, message, params)

        self.__class__.objects.filter(id=self.id).update(**options)
        self.refresh_from_db()

        logger.info(
            "Updated %s: %d with state: %s",
            self.__class__.__name__,
            self.id,
            options["state"],
        )


class Order(UserOwnedModel, MessageableMixin, KeycloakMixin):
    """Order object to wrap order items."""

    KEYCLOAK_TYPE = "catalog:order"

    class State(models.TextChoices):
        """Available states for Order"""

        PENDING = gettext_noop("Approval Pending")
        APPROVED = gettext_noop("Approved")
        CANCELED = gettext_noop("Canceled")
        COMPLETED = gettext_noop("Completed")
        CREATED = gettext_noop("Created")
        DENIED = gettext_noop("Denied")
        FAILED = gettext_noop("Failed")
        ORDERED = gettext_noop("Ordered")

    state = models.CharField(
        max_length=20,
        choices=State.choices,
        default=State.CREATED,
        editable=False,
        help_text="Current state of the order",
    )
    order_request_sent_at = models.DateTimeField(
        editable=False,
        null=True,
        help_text=(
            "The time at which the order request was sent to the catalog"
            " inventory service"
        ),
    )
    completed_at = models.DateTimeField(
        editable=False,
        null=True,
        help_text="The time at which the order completed",
    )

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
        from pinakes.main.catalog.services.sanitize_parameters import (
            SanitizeParameters,
        )

        portfolio_item = kwargs["portfolio_item"]
        service_plan = ServicePlan.objects.filter(
            portfolio_item=portfolio_item
        ).first()

        kwargs["name"] = portfolio_item.name

        if (
            service_plan
            and service_plan.inventory_service_plan_ref
            and "service_parameters" in kwargs
        ):
            kwargs[
                "inventory_service_plan_ref"
            ] = service_plan.inventory_service_plan_ref
            sanitized_parameters = (
                SanitizeParameters(service_plan, kwargs["service_parameters"])
                .process()
                .sanitized_parameters
            )
            if kwargs["service_parameters"] != sanitized_parameters:
                kwargs["service_parameters_raw"] = kwargs["service_parameters"]
                kwargs["service_parameters"] = sanitized_parameters

        return super(OrderItemManager, self).create(*args, **kwargs)


class OrderItem(UserOwnedModel, MessageableMixin):
    """Order Item Model"""

    class State(models.TextChoices):
        """Available states for Order Item"""

        PENDING = gettext_noop("Approval Pending")
        APPROVED = gettext_noop("Approved")
        CANCELED = gettext_noop("Canceled")
        COMPLETED = gettext_noop("Completed")
        CREATED = gettext_noop("Created")
        DENIED = gettext_noop("Denied")
        FAILED = gettext_noop("Failed")
        ORDERED = gettext_noop("Ordered")

    FINISHED_STATES = [
        State.COMPLETED,
        State.CANCELED,
        State.FAILED,
        State.DENIED,
    ]

    objects = OrderItemManager()
    name = models.CharField(
        max_length=PortfolioItem.MAX_PORTFOLIO_ITEM_LENGTH,
        help_text="Name of the portfolio item or order process",
    )
    state = models.CharField(
        max_length=20,
        choices=State.choices,
        default=State.CREATED,
        editable=False,
        help_text="Current state of this order item",
    )
    order_request_sent_at = models.DateTimeField(
        editable=False,
        null=True,
        help_text=(
            "The time at which the order request was sent to the catalog"
            " inventory service"
        ),
    )
    completed_at = models.DateTimeField(
        editable=False,
        null=True,
        help_text="The time at which the order item completed",
    )
    count = models.SmallIntegerField(
        editable=False, default=0, help_text="Item count"
    )
    inventory_task_ref = models.CharField(
        max_length=64, null=True, help_text="Task reference from inventory-api"
    )
    inventory_service_plan_ref = models.CharField(
        max_length=64,
        null=True,
        help_text="Corresponding service plan from inventory-api",
    )
    service_instance_ref = models.CharField(
        max_length=64,
        null=True,
        help_text="Corresponding service instance from inventory-api",
    )
    service_parameters = models.JSONField(
        blank=True,
        null=True,
        help_text="Sanitized JSON object with provisioning parameters",
    )
    service_parameters_raw = models.JSONField(
        blank=True,
        null=True,
        help_text="Raw JSON object with provisioning parameters",
    )
    provider_control_parameters = models.JSONField(
        blank=True,
        null=True,
        help_text=(
            "The provider specific parameters needed to provision this"
            " service. This might include namespaces, special keys."
        ),
    )
    context = models.JSONField(blank=True, null=True)
    artifacts = models.JSONField(
        blank=True,
        null=True,
        help_text=(
            "Contains a prefix-stripped key/value object that contains all of"
            " the information exposed from product provisioning"
        ),
    )
    external_url = models.URLField(
        blank=True,
        help_text=(
            "The external url of the service instance used with relation to"
            " this order item"
        ),
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        help_text="The order that the order item belongs to",
    )
    portfolio_item = models.ForeignKey(
        PortfolioItem,
        on_delete=models.CASCADE,
        help_text="Stores the portfolio item ID",
    )

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
        message = gettext_noop(
            "Created Approval Request ref: %(approval_request_ref)s. \
Catalog approval request id: %(approval_request_id)s"
        )
        params = {
            "approval_request_ref": approval_request_ref,
            "approval_request_id": str(approval_request.id),
        }
        approval_request.order.update_message(
            ProgressMessage.Level.INFO, message, params
        )

        return approval_request


class ApprovalRequest(BaseModel):
    """Approval Request Model"""

    class State(models.TextChoices):
        """Available states for approval request"""

        UNDECIDED = gettext_noop("undecided")
        APPROVED = gettext_noop("approved")
        CANCELED = gettext_noop("canceled")
        DENIED = gettext_noop("denied")
        FAILED = gettext_noop("failed")

    objects = ApprovalRequestManager()
    approval_request_ref = models.CharField(
        max_length=64,
        default="",
        help_text="The ID of the approval submitted to approval-api",
    )
    reason = models.TextField(
        blank=True,
        default="",
        help_text="The reason for the current state",
    )
    request_completed_at = models.DateTimeField(
        editable=False,
        null=True,
        help_text="The time at which the approval request completed",
    )
    state = models.CharField(
        max_length=10,
        choices=State.choices,
        default=State.UNDECIDED,
        editable=False,
        help_text=(
            "The state of the approval request (approved, denied, undecided,"
            " canceled, error)"
        ),
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        help_text="The Order which the approval request belongs to",
    )

    class Meta:
        indexes = [models.Index(fields=["tenant", "order"])]

    def __str__(self):
        return str(self.id)


class ServicePlan(KeycloakMixin, BaseModel):
    """Service Plan Model"""

    KEYCLOAK_TYPE = "catalog:service_plan"

    name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="The name of the service plan",
    )
    base_schema = models.JSONField(
        blank=True,
        null=True,
        help_text="JSON schema of the survey from the controller",
    )
    modified_schema = models.JSONField(
        blank=True,
        null=True,
        help_text="Modified JSON schema for the service plan",
    )
    base_sha256 = models.TextField(
        blank=True,
        default="",
        editable=False,
        help_text="SHA256 of the base schema",
    )
    outdated = models.BooleanField(
        default=False,
        editable=False,
        help_text=(
            "Whether or not the base schema is outdated. The portfolio item is"
            " not orderable if the base schema is outdated."
        ),
    )
    outdated_changes = models.TextField(
        blank=True,
        default="",
        editable=False,
        help_text="Changes of the base schema from inventory since last edit",
    )
    inventory_service_plan_ref = models.CharField(
        max_length=64,
        null=True,
        help_text="Corresponding service plan from inventory-api",
    )
    service_offering_ref = models.CharField(
        max_length=64,
        null=True,
        help_text="Corresponding service offering from inventory-api",
    )

    portfolio_item = models.ForeignKey(
        PortfolioItem,
        on_delete=models.CASCADE,
        help_text="ID of the portfolio item",
    )

    class Meta:
        indexes = [models.Index(fields=["tenant", "portfolio_item"])]

    @property
    def schema(self):
        """The active schema of parameters for provisioning a portfolio item"""
        return self.modified_schema or self.base_schema

    @property
    def modified(self):
        """Indicates whether the schema has been modified by user"""
        return self.modified_schema is not None

    def __str__(self):
        return self.name
