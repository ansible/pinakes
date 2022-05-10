"""Test email notification"""
from unittest.mock import Mock
from unittest.mock import patch
import pytest

from pinakes.main.tests.factories import UserFactory
from pinakes.main.approval.tests.factories import (
    NotificationSettingFactory,
    TemplateFactory,
    WorkflowFactory,
    RequestFactory,
    RequestContextFactory,
)
from pinakes.main.approval.services.email_notification import EmailNotification
from pinakes.main.catalog.services.handle_approval_events import (
    HandleApprovalEvents,
)


@pytest.mark.django_db
def test_email_notification(mocker):
    """Test sending emails"""
    email_settings = {
        "host": "smtp.test.com",
        "port": 123,
        "security": "use_tls",
        "from": "catalog@test.com",
        "ssl_key": "keyval",
        "ssl_cert": "certificate",
    }
    content = {
        "product": "feature product",
        "portfolio": "feature portfolio",
        "order_id": "1",
        "platform": "feature AAP",
        "params": {"key": "val"},
    }
    context = {"http_host": "test.com"}
    request_context = RequestContextFactory(content=content, context=context)

    group_ref = "group_uuid"
    user = UserFactory(
        email="user@test.com", first_name="wilma", last_name="Smith"
    )
    ns = NotificationSettingFactory(settings=email_settings)
    template = TemplateFactory(process_method=ns)
    workflow = WorkflowFactory(template=template)
    request = RequestFactory(
        state="started",
        workflow=workflow,
        group_ref=group_ref,
        request_context=request_context,
        user=user,
    )

    admin = Mock()
    approver = Mock(email="qa@test.com", firstName="Fred", lastName="Smith")
    admin.list_group_members.return_value = [approver]
    mocker.patch(
        "pinakes.main.approval.services.email_notification.get_admin_client",
        return_value=admin,
    )

    with patch(
        "pinakes.main.approval.services.email_notification.send_mail"
    ) as send_mail_call:
        EmailNotification(request).send_emails()
        args = send_mail_call.call_args[1]
        assert args["from_email"] == "catalog@test.com"
        assert args["recipient_list"][0] == approver.email
        assert args["connection"].host == email_settings["host"]
        assert args["connection"].port == email_settings["port"]
        assert args["connection"].use_tls is True
        assert args["connection"].timeout == 20
        assert args["connection"].ssl_keyfile is not None
        assert args["connection"].ssl_certfile is not None
        assert bool("</html>" in args["html_message"]) is True
        assert bool("$" in args["html_message"]) is False
        assert request.state == "notified"

    mocker.patch.object(HandleApprovalEvents, "process", return_value=None)
    with patch(
        "pinakes.main.approval.services.email_notification.send_mail"
    ) as send_mail_call:
        send_mail_call.side_effect = Exception()
        EmailNotification(request).send_emails()
        assert request.state == "failed"
