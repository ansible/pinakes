"""Models for Approval"""
from django.db import models
from django.db.models.functions import Length
from django.contrib.auth import get_user_model
from django.core.signing import Signer

from pinakes.common.models.fields import EncryptedJsonField
from pinakes.main.models import BaseModel, ImageableModel
from pinakes.common.auth.keycloak_django.models import KeycloakMixin
from pinakes.common.auth.keycloak_django import AbstractKeycloakResource

models.CharField.register_lookup(Length)


# pylint: disable=no-member
class NotificationType(ImageableModel, models.Model):
    """NotificationType model"""

    n_type = models.CharField(
        max_length=128,
        unique=True,
        help_text="Name of the notification type",
    )
    setting_schema = models.JSONField(
        blank=True,
        null=True,
        help_text="JSON schema of the notification type",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_n_type_empty",
                check=models.Q(n_type__length__gt=0),
            ),
        ]

    def __str__(self):
        return self.n_type


class SettingField(models.TextField):
    """Customized field to store encrypted settings"""

    def get_prep_value(self, value):
        """override"""
        if value is None:
            return None
        return Signer().sign_object(value)

    def from_db_value(self, value, _expression, _connection):
        """override"""
        if value is None:
            return None
        return Signer().unsign_object(value)

    def to_python(self, value):
        """override"""
        if value is None:
            return None
        return Signer().unsign_object(value)


class NotificationSetting(BaseModel):
    """Notification setting"""

    name = models.CharField(
        max_length=128,
        editable=True,
        help_text="Name of the notification method",
    )
    settings = EncryptedJsonField(
        null=True,
        help_text="Parameters for configuring the notification method",
    )
    notification_type = models.ForeignKey(
        NotificationType,
        null=True,
        on_delete=models.CASCADE,
        help_text="ID of the notification type",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_name_empty",
                check=models.Q(name__length__gt=0),
            ),
            models.UniqueConstraint(
                name="%(app_label)s_%(class)s_name_unique",
                fields=("name", "tenant"),
            ),
        ]

    def __str__(self):
        return self.name


class Template(KeycloakMixin, BaseModel):
    """Template model"""

    KEYCLOAK_TYPE = "approval:template"

    title = models.CharField(max_length=255, help_text="Name of the template")
    description = models.TextField(
        blank=True,
        default="",
        help_text="Describe the template with more details",
    )
    process_method = models.ForeignKey(
        NotificationSetting,
        null=True,
        related_name="process_notification",
        on_delete=models.CASCADE,
        help_text="ID of the notification method for processing the workflow",
    )
    signal_method = models.ForeignKey(
        NotificationSetting,
        null=True,
        on_delete=models.CASCADE,
        related_name="signal_notification",
        help_text=(
            "ID of the notification method for signaling the completion of the"
            " workflow",
        ),
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_title_empty",
                check=models.Q(title__length__gt=0),
            ),
            models.UniqueConstraint(
                name="%(app_label)s_%(class)s_title_unique",
                fields=["title", "tenant"],
            ),
        ]

    def __str__(self):
        return self.title


class Workflow(KeycloakMixin, BaseModel):
    """Workflow model"""

    KEYCLOAK_TYPE = "approval:workflow"
    INTERNAL_INTERVAL = 1024  # an integer must be greater than 1

    name = models.CharField(max_length=255, help_text="Name of the workflow")
    description = models.TextField(
        blank=True,
        default="",
        help_text="Describe the workflow in more details",
    )
    group_refs = models.JSONField(
        default=list,
        help_text=(
            "Array of RBAC groups associated with workflow. The groups need to"
            " have approval permission"
        ),
    )
    internal_sequence = models.BigIntegerField(db_index=True)
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        help_text="ID of the template that the workflow belongs to",
    )

    class Meta:
        ordering = ["internal_sequence"]
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_name_empty",
                check=models.Q(name__length__gt=0),
            ),
            models.UniqueConstraint(
                name="%(app_label)s_%(class)s_name_unique",
                fields=["name", "tenant", "template"],
            ),
            models.UniqueConstraint(
                name="%(app_label)s_%(class)s_internal_sequence_unique",
                fields=["internal_sequence", "tenant"],
            ),
        ]

    def move_internal_sequence(self, delta):
        """
        Move current record up or down relative to other records.
        delta is an integer indictating how many other records should this
        record be moved over upward (negative) or downward (positive).

        Internal_sequence is a column used to sort the workflows by users.
        The user only needs to be able to adjust the sequence of the workflow
        but does not care the actual value of the internal_sequence. When a new
        workflow is created it is placed to the end of the list with an
        internal_sequence number much greater than the value from previous tail
        of the list. When workflow_a is moved to between workflow_b and
        workflow_c, its internal_sequence is simply adjusted to the average
        number of b and c unless the average becomes a decimal, in which case
        all the internal_sequence numbers will get rebalanced with a big
        interval again.
        """
        if delta == 0:
            return

        if delta > 0:
            self.internal_sequence = self._internal_sequence_plus(delta)
        else:
            self.internal_sequence = self._internal_sequence_minus(-delta)

    def _internal_sequence_plus(self, delta):
        query = Workflow.objects.filter(
            internal_sequence__gt=self.internal_sequence
        )
        sequence_range = self._internal_sequence_range(query, delta)

        if len(sequence_range) == 0:
            return self._internal_sequence_extend_from_last()

        if len(sequence_range) == 1:
            return sequence_range[0] + Workflow.INTERNAL_INTERVAL

        if sequence_range[1] - sequence_range[0] < 2:
            self._rebalance_internal_sequences()
            return self._internal_sequence_plus(delta)

        return (sequence_range[0] + sequence_range[1]) // 2

    def _internal_sequence_minus(self, delta):
        query = Workflow.objects.filter(
            internal_sequence__lt=self.internal_sequence
        ).order_by("-internal_sequence")
        sequence_range = self._internal_sequence_range(query, delta)
        if len(sequence_range) == 0:
            return self._internal_sequence_before_first()

        if len(sequence_range) == 1:
            return self._half_first_internal_sequence(sequence_range[0])

        if sequence_range[0] - sequence_range[1] < 2:
            self._rebalance_internal_sequences()
            return self._internal_sequence_minus(delta)

        return (sequence_range[0] + sequence_range[1]) // 2

    def _internal_sequence_range(self, query, delta):
        return query.values_list("internal_sequence", flat=True)[
            (delta - 1) : (delta + 1)
        ]

    def _internal_sequence_extend_from_last(self):
        last_sequence = (
            Workflow.objects.filter(tenant=self.tenant)
            .values_list("internal_sequence", flat=True)
            .last()
        )
        return last_sequence + Workflow.INTERNAL_INTERVAL

    def _internal_sequence_before_first(self):
        first_sequence = (
            Workflow.objects.filter(tenant=self.tenant)
            .values_list("internal_sequence", flat=True)
            .first()
        )
        return self._half_first_internal_sequence(first_sequence)

    def _half_first_internal_sequence(self, first_sequence):
        if first_sequence < 2:
            self._rebalance_internal_sequences()
            return Workflow.INTERNAL_INTERVAL // 2
        return first_sequence // 2

    def _rebalance_internal_sequences(self):
        workflows = Workflow.objects.filter(tenant=self.tenant)
        new_sequence = 0
        for workflow in workflows:
            new_sequence = new_sequence + Workflow.INTERNAL_INTERVAL
            workflow.internal_sequence = new_sequence

        Workflow.objects.bulk_update(workflows, ["internal_sequence"])
        self.refresh_from_db()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.internal_sequence is None:
            max_obj = Workflow.objects.filter(tenant=self.tenant).last()
            if max_obj is None:
                self.internal_sequence = Workflow.INTERNAL_INTERVAL
            else:
                self.internal_sequence = (
                    max_obj.internal_sequence + Workflow.INTERNAL_INTERVAL
                )
        super().save(*args, **kwargs)


class RequestContext(models.Model):
    """RequestContext model"""

    content = models.JSONField()
    context = models.JSONField()


class Request(AbstractKeycloakResource, BaseModel):
    """Request model"""

    KEYCLOAK_TYPE = "approval:request"
    KEYCLOAK_ACTIONS = ("read",)

    class State(models.TextChoices):
        """State contants"""

        PENDING = "pending"
        SKIPPED = "skipped"
        STARTED = "started"
        NOTIFIED = "notified"
        COMPLETED = "completed"
        CANCELED = "canceled"
        FAILED = "failed"

    class Decision(models.TextChoices):
        """Decision constants"""

        UNDECIDED = "undecided"
        APPROVED = "approved"
        DENIED = "denied"
        CANCELED = "canceled"
        ERROR = "error"

    name = models.CharField(
        max_length=255,
        help_text="Name of the request to be created",
    )
    description = models.TextField(
        blank=True,
        help_text="Describe the request in more details",
    )
    state = models.CharField(
        max_length=10,
        choices=State.choices,
        default=State.PENDING,
        editable=False,
        help_text=(
            "The state of the request, must be one of the predefined values"
        ),
    )
    decision = models.CharField(
        max_length=10,
        choices=Decision.choices,
        default=Decision.UNDECIDED,
        editable=False,
        help_text="Approval decision, must be one of the predefined values",
    )
    reason = models.TextField(
        blank=True,
        editable=False,
        help_text=(
            "Optional reason for the decision, present normally when the"
            " decision is denied"
        ),
    )
    process_ref = models.CharField(max_length=128, editable=False)
    group_name = models.CharField(
        max_length=128,
        editable=False,
        help_text="Name of approver group(s) assigned to approve this request",
    )
    group_ref = models.CharField(max_length=128, editable=False, db_index=True)
    notified_at = models.DateTimeField(
        editable=False,
        null=True,
        help_text="Time when a notification was sent to approvers",
    )
    finished_at = models.DateTimeField(
        editable=False,
        null=True,
        help_text=(
            "Time when the request was finished (skipped, canceled, or"
            " completed)"
        ),
    )
    number_of_children = models.SmallIntegerField(
        editable=False,
        default=0,
        help_text="Number of child requests",
    )
    number_of_finished_children = models.SmallIntegerField(
        editable=False,
        default=0,
        help_text="Number of finished child requests",
    )
    workflow = models.ForeignKey(
        Workflow,
        null=True,
        on_delete=models.SET_NULL,
        help_text=(
            "ID of the workflow that the request belongs to. Present only if"
            " the request is a leaf node"
        ),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        related_name="subrequests",
        help_text="ID of the parent group if present",
    )
    request_context = models.ForeignKey(
        RequestContext, null=True, on_delete=models.SET_NULL
    )
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True
    )

    @property
    def requester_name(self):
        """Full name of the requester"""
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def owner(self):
        """Identification of whom made the request"""
        return f"{self.user.username}"

    @property
    def requests(self):
        """get child requests"""
        return self.__class__.objects.filter(parent=self)

    def invalidate_number_of_children(self):
        """update number of children"""
        self.number_of_children = self.requests.count()
        self.save()

    def invalidate_number_of_finished_children(self):
        """update number of finished children"""
        if self.number_of_children > 0:
            count = 0
            for child in self.requests:
                if child.has_finished():
                    count += 1
            self.number_of_finished_children = count
            self.save()

    def create_child(self):
        """create a child request"""
        child = self.__class__.objects.create(
            tenant=self.tenant,
            name=self.name,
            description=self.description,
            user=self.user,
            parent=self,
            request_context=self.request_context,
        )
        self.invalidate_number_of_children()
        return child

    def is_root(self):
        """Is the request a root node"""
        return not bool(self.parent)

    def is_leaf(self):
        """Is the request a leaf node"""
        return self.number_of_children == 0

    def is_child(self):
        """Is the request a child of a parent request"""
        return not self.is_root()

    def is_parent(self):
        """Is the request a parent request that has child requests"""
        return self.number_of_children > 0

    def root(self):
        """Return the root request of current request"""
        return self if self.is_root() else self.parent

    def has_finished(self):
        """Is the request in finished state?"""
        return self.state in (
            self.State.COMPLETED,
            self.State.SKIPPED,
            self.State.CANCELED,
            self.State.FAILED,
        )

    def can_cancel(self) -> bool:
        """Is the request in a state that can be canceled"""
        return self.is_root() and self.state in (
            self.State.PENDING,
            self.State.STARTED,
            self.State.NOTIFIED,
        )

    def can_decide(self) -> bool:
        """Is the request in a state that can be approved or denied"""
        return self.is_leaf() and self.state == self.State.NOTIFIED

    def __str__(self):
        return self.name


class Action(BaseModel):
    """Action model"""

    class Operation(models.TextChoices):
        """Operation contants"""

        NOTIFY = "notify"
        START = "start"
        SKIP = "skip"
        MEMO = "memo"
        APPROVE = "approve"
        DENY = "deny"
        CANCEL = "cancel"
        ERROR = "error"

    operation = models.CharField(
        max_length=10,
        choices=Operation.choices,
        default=Operation.MEMO,
        help_text=(
            "Action type, must be one of the predefined values. The request"
            " state will be updated according to the operation."
        ),
    )
    comments = models.TextField(
        blank=True, help_text="Comments for the action"
    )
    request = models.ForeignKey(
        Request,
        on_delete=models.CASCADE,
        related_name="actions",
        help_text="ID of the request that the action belongs to",
    )
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, null=True
    )

    @property
    def processed_by(self):
        """virtual column processed_by"""
        if not self.user:
            return "system"
        return (
            f"{self.user.first_name} {self.user.last_name}"
            if self.user.first_name
            else self.user.username
        )

    def __str__(self):
        return self.operation


class TagLink(BaseModel):
    """TagLink model"""

    app_name = models.CharField(max_length=128, editable=False)
    tag_name = models.CharField(max_length=128, editable=False)
    object_type = models.CharField(max_length=32, editable=False)

    workflow = models.ForeignKey(
        Workflow, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name="%(app_label)s_%(class)s_tag_unique",
                fields=["app_name", "object_type", "tenant", "workflow"],
            ),
        ]

    def __str__(self):
        return self.tag_name
