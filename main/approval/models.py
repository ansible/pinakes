"""Models for Approval"""
from django.db import models
from django.db.models.functions import Length
from django.contrib.auth.models import User

from main.models import BaseModel

models.CharField.register_lookup(Length)


class Template(BaseModel):
    """Template model"""

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
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

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    group_refs = models.JSONField(default=list)
    internal_sequence = models.DecimalField(
        max_digits=16, decimal_places=6, db_index=True
    )
    template = models.ForeignKey(Template, on_delete=models.CASCADE)

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


class RequestManager(models.Manager):
    """Override default manager with create method"""

    def create(self, *args, **kwargs):
        # TODO: find workflow based on tag resources
        tag_resources = kwargs.pop("tag_resources", None)
        if tag_resources is not None:
            pass

        request_context = kwargs.pop("request_context", None)

        if request_context is None:
            content = kwargs.pop("content", None)
            request_context = (
                RequestContext.objects.create(content=content, context={})
                if content is not None
                else None
            )

        return super(RequestManager, self).create(
            request_context=request_context, **kwargs
        )


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

    objects = RequestManager()
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    state = models.CharField(
        max_length=10,
        choices=State.choices,
        default=State.PENDING,
        editable=False,
    )
    decision = models.CharField(
        max_length=10,
        choices=Decision.choices,
        default=Decision.UNDECIDED,
        editable=False,
    )
    reason = models.TextField(blank=True, editable=False)
    process_ref = models.CharField(max_length=128, editable=False)
    group_name = models.CharField(max_length=128, editable=False)
    group_ref = models.CharField(max_length=128, editable=False, db_index=True)
    notified_at = models.DateTimeField(editable=False, null=True)
    finished_at = models.DateTimeField(editable=False, null=True)
    number_of_children = models.SmallIntegerField(editable=False, default=0)
    number_of_finished_children = models.SmallIntegerField(
        editable=False, default=0
    )
    workflow = models.ForeignKey(
        Workflow, null=True, on_delete=models.SET_NULL
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        related_name="sub_requests",
    )
    request_context = models.ForeignKey(
        RequestContext, null=True, on_delete=models.SET_NULL
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    @property
    def requester_name(self):
        """virtual column requester_name"""
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def owner(self):
        """virtual column owner"""
        return f"{self.user.username}"

    def __str__(self):
        return self.name


class Action(BaseModel):
    """Action model"""

    class Operation(models.TextChoices):
        NOTIFY = "Notify"
        START = "Start"
        SKIP = "Skip"
        Memo = "Memo"
        APPROVE = "Approve"
        DENY = "Deny"
        CANCEL = "Cancel"
        ERROR = "Error"

    processed_by = models.CharField(max_length=128, editable=False)
    operation = models.CharField(
        max_length=10, choices=Operation.choices, default=Operation.Memo
    )
    comments = models.TextField(blank=True)
    request = models.ForeignKey(
        Request, on_delete=models.CASCADE, related_name="actions"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    @property
    def processed_by(self):
        """virtual column processed_by"""
        return f"{self.user.first_name} {self.user.last_name}"

    def __str__(self):
        return self.operation
