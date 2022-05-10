"""Email notification for an approval request"""
import logging
import string
import django_rq
import tempfile
from importlib.resources import read_text
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend

from pinakes.common.auth.keycloak_django.clients import get_admin_client
from pinakes.main.approval.services.create_action import CreateAction
from pinakes.main.approval.models import Action, Request


logger = logging.getLogger("approval")


class EmailNotification:
    """Service class for email notification"""

    def __init__(self, request):
        self.request = (
            request
            if isinstance(request, Request)
            else Request.objects.get(id=request)
        )

    def process(self):
        """process the service"""
        from pinakes.main.approval.tasks import email_task

        self.job = django_rq.enqueue(email_task, self.request.id)
        logger.info(
            "Enqueued job %s for sending email notification for request %d",
            self.job.id,
            self.request.id,
        )
        return self

    def send_emails(self):
        settings = self.request.workflow.template.process_method.settings
        sender = settings.pop("from", None)
        security = settings.pop("security", None)
        has_cert = False
        if security:
            settings[security] = True
            ssl_key = settings.pop("ssl_key", None)
            ssl_cert = settings.pop("ssl_cert", None)
            if ssl_key and ssl_cert:
                key_file = tempfile.NamedTemporaryFile(mode="w+t")
                key_file.write(ssl_key)
                key_file.flush()
                settings["ssl_keyfile"] = key_file.name
                cert_file = tempfile.NamedTemporaryFile(mode="w+t")
                cert_file.write(ssl_cert)
                cert_file.flush()
                settings["ssl_certfile"] = cert_file.name
                has_cert = True
        if "timeout" not in settings:
            settings["timeout"] = 20
        backend = EmailBackend(**settings)

        group_id = self.request.group_ref
        approvers = get_admin_client().list_group_members(group_id, 0, 100)
        all_failed = True
        for approver in approvers:
            logger.info("Sending email to %s", approver.email)
            try:
                send_mail(
                    subject=self._subject(),
                    message=self._plain_body(),
                    html_message=self._html_body(approver),
                    from_email=sender,
                    recipient_list=(approver.email,),
                    connection=backend,
                )
                all_failed = False
            except Exception as ex:
                logger.error("Email failed. Error %s", ex)
        backend.close()
        if has_cert:
            cert_file.close()
            key_file.close()

        if all_failed:
            CreateAction(
                self.request,
                {
                    "operation": Action.Operation.ERROR,
                    "comments": _("Failed to email group {}").format(
                        self.request.group_name
                    ),
                },
            ).process()
        else:
            CreateAction(
                self.request, {"operation": Action.Operation.NOTIFY}
            ).process()

    def _subject(self):
        return (
            f"Catalog:Approval Order {self.request.id}: "
            f"{self.request.requester_name}"
        )

    def _plain_body(self):
        return (
            "There is a Pinakes order requires your approval. "
            f"Please visit {self._web_url()}/{self._approval_link()}."
        )

    def _html_body(self, approver):
        content = self.request.request_context.content
        params = {
            "approval_id": self.request.id,
            "approver_name": f"{approver.firstName} {approver.lastName}",
            "group_name": self.request.group_name,
            "orderer_email": self.request.user.email,
            "requester_name": self.request.requester_name,
            "order_id": content["order_id"],
            "order_date": self.request.created_at.strftime("%m/%d/%Y"),
            "order_time": self.request.created_at.strftime("%H:%M:%S"),
            "product": content["product"],
            "portfolio": content["portfolio"],
            "platform": content["platform"],
            "approve_link": self._approval_link(),
            "web_url": self._web_url(),
        }
        email_template = read_text("pinakes.data", "email_template.html")
        return string.Template(email_template).safe_substitute(**params)

    def _web_url(self):
        return self.request.request_context.context.get(
            "http_host", "localhost"
        )

    def _approval_link(self):
        return f"ui/catalog/approval/request?request={self.request.id}"
