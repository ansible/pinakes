"""Models for Approval"""
from django.db import models
from django.db.models.functions import Length
from django.contrib.auth.models import User
from drf_spectacular.utils import OpenApiTypes

from ansible_catalog.main.models import BaseModel

models.CharField.register_lookup(Length)


class Template(BaseModel):
    """Template model"""

    title = models.CharField(max_length=255, help_text="Name of the template")
    description = models.TextField(
        blank=True,
        default="",
        help_text="Describe the template with more details",
    )
    process_setting = models.JSONField(blank=True, null=True)
    signal_setting = models.JSONField(blank=True, null=True)

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


class Workflow(BaseModel):
    """Workflow model"""

    name = models.CharField(max_length=255, help_text="Name of the workflow")
    description = models.TextField(
        blank=True,
        default="",
        help_text="Describe the workflow in more details",
    )
    group_refs = models.JSONField(
        default=list,
        help_text="Array of RBAC groups associated with workflow. The groups need to have approval permission",
    )
    internal_sequence = models.DecimalField(
        max_digits=16, decimal_places=6, db_index=True
    )
    template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        help_text="ID of the template that the workflow belongs to",
    )

    class Meta:
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

    def __str__(self):
        return self.name


class RequestContext(models.Model):
    content = models.JSONField()
    context = models.JSONField()


class Request(BaseModel):
    """Request model"""

    class State(models.TextChoices):
        PENDING = "Pending"
        SKIPPED = "Skipped"
        STARTED = "Started"
        NOTIFIED = "Notified"
        COMPLETED = "Completed"
        CANCELED = "Canceled"
        FAILED = "Failed"

    class Decision(models.TextChoices):
        UNDECIDED = "Undecided"
        APPROVED = "Approved"
        DENIED = "Denied"
        CANCELED = "Canceled"
        ERROR = "Error"

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
        help_text="The state of the request, must be one of the predefined values",
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
        help_text="Optional reason for the decision, present normally when the decision is denied",
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
        help_text="Time when the request was finished (skipped, canceled, or completed)",
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
        help_text="ID of the workflow that the request belongs to. Present only if the request is a leaf node",
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

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
        return False if self.parent else True

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

    def __str__(self):
        return self.name


class Action(BaseModel):
    """Action model"""

    class Operation(models.TextChoices):
        NOTIFY = "Notify"
        START = "Start"
        SKIP = "Skip"
        MEMO = "Memo"
        APPROVE = "Approve"
        DENY = "Deny"
        CANCEL = "Cancel"
        ERROR = "Error"

    operation = models.CharField(
        max_length=10,
        choices=Operation.choices,
        default=Operation.MEMO,
        help_text="Action type, must be one of the predefined values. The request state will be updated according to the operation.",
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

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
