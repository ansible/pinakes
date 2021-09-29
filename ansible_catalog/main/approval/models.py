"""Models for Approval"""
from django.db import models
from django.db.models.functions import Length
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

from ansible_catalog.main.models import BaseModel

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
        related_name="subrequests",
    )
    request_context = models.ForeignKey(
        RequestContext, null=True, on_delete=models.SET_NULL
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    @property
    @extend_schema_field(OpenApiTypes.STR)
    def requester_name(self):
        """virtual column requester_name"""
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    @extend_schema_field(OpenApiTypes.STR)
    def owner(self):
        """virtual column owner"""
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
        max_length=10, choices=Operation.choices, default=Operation.MEMO
    )
    comments = models.TextField(blank=True)
    request = models.ForeignKey(
        Request, on_delete=models.CASCADE, related_name="actions"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    @property
    @extend_schema_field(OpenApiTypes.STR)
    def processed_by(self):
        """virtual column processed_by"""
        return f"{self.user.first_name} {self.user.last_name}"

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
