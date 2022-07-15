"""Collection of factory classes for approval models"""
import factory

from pinakes.main.approval.models import (
    NotificationType,
    NotificationSetting,
    Template,
    Workflow,
    Request,
    RequestContext,
    Action,
)
from pinakes.main.tests.factories import default_tenant


class NotificationTypeFactory(factory.django.DjangoModelFactory):
    """Notification type factory class"""

    class Meta:
        model = NotificationType

    n_type = factory.Sequence(lambda n: f"notificationtype{n}")


class NotificationSettingFactory(factory.django.DjangoModelFactory):
    """Notification setting factory class"""

    class Meta:
        model = NotificationSetting

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    notification_type_id = 1  # the default seeded one
    name = factory.Sequence(lambda n: f"notificationsetting{n}")


class TemplateFactory(factory.django.DjangoModelFactory):
    """Template factory class"""

    class Meta:
        model = Template

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    title = factory.Sequence(lambda n: f"title{n}")
    description = factory.Sequence(lambda n: f"title{n}_description")


class WorkflowFactory(factory.django.DjangoModelFactory):
    """Workflow factory class"""

    class Meta:
        model = Workflow

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    template = factory.SubFactory(TemplateFactory)
    name = factory.Sequence(lambda n: f"workflow{n}")
    description = factory.Sequence(lambda n: f"workflow{n}_description")


class RequestFactory(factory.django.DjangoModelFactory):
    """Request factory class"""

    class Meta:
        model = Request

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    workflow = factory.SubFactory(WorkflowFactory)


class RequestContextFactory(factory.django.DjangoModelFactory):
    """RequestContext factory class"""

    class Meta:
        model = RequestContext

    context = {}


class ActionFactory(factory.django.DjangoModelFactory):
    """Action factory class"""

    class Meta:
        model = Action

    tenant = factory.LazyAttribute(lambda _: default_tenant())
    request = factory.SubFactory(RequestFactory)
