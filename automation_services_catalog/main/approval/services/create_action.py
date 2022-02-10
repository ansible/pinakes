"""Service to create various types of action"""

from django.utils.translation import gettext_lazy as _

from automation_services_catalog.main.approval.models import (
    Action,
    Request,
)
from automation_services_catalog.main.approval.exceptions import (
    InvalidStateTransitionException,
    BlankParameterException,
)


class CreateAction:
    """Service class to create actions"""

    def __init__(self, request, options):
        self.options = options
        self.request = (
            request
            if isinstance(request, Request)
            else Request.objects.get(id=request)
        )
        self.action = None

    def process(self):
        from automation_services_catalog.main.approval.services.update_request import (
            UpdateRequest,
        )

        operation = self.options["operation"].lower()
        request_options = getattr(self, f"_{operation}")(
            self.options.get("comments")
        )

        self.options["request"] = self.request
        self.options["tenant"] = self.request.tenant
        self.action = Action.objects.create(**self.options)

        if request_options:
            UpdateRequest(self.request, request_options).process()

        return self

    def _memo(self, comments):
        if not comments:
            raise BlankParameterException(
                _("The memo message cannot be blank")
            )
        return {}

    def _start(self, _comments):
        if not self.request.state == Request.State.PENDING:
            raise InvalidStateTransitionException(
                _("Current request is not pending state")
            )

        return {"state": Request.State.STARTED}

    def _notify(self, _comments):
        if not self.request.state == Request.State.STARTED:
            raise InvalidStateTransitionException(
                _("Current request is not started state")
            )

        return {"state": Request.State.NOTIFIED}

    def _skip(self, _comments):
        if not self.request.state == Request.State.PENDING:
            raise InvalidStateTransitionException(
                _("Current request is not in pending state")
            )

        return {"state": Request.State.SKIPPED}

    def _approve(self, comments):
        if not self.request.state == Request.State.NOTIFIED:
            raise InvalidStateTransitionException(
                _("Current request is not in notified state")
            )

        if self.request.is_parent():
            raise InvalidStateTransitionException(
                _("Only child level request can be approved")
            )

        return {
            "state": Request.State.COMPLETED,
            "decision": Request.Decision.APPROVED,
            "reason": comments,
        }

    def _deny(self, comments):
        if not self.request.state == Request.State.NOTIFIED:
            raise InvalidStateTransitionException(
                _("Current request is not in notified state")
            )

        if self.request.is_parent():
            raise InvalidStateTransitionException(
                _("Only child level request can be denied")
            )

        if not comments:
            raise BlankParameterException(
                _("A reason has to be provided if a request is being denied")
            )

        return {
            "state": Request.State.COMPLETED,
            "decision": Request.Decision.DENIED,
            "reason": comments,
        }

    def _cancel(self, comments):
        if not self.request.is_root():
            raise InvalidStateTransitionException(
                _("Only root level request can be canceled")
            )

        if self.request.has_finished():
            raise InvalidStateTransitionException(
                _("The request has already finished")
            )

        return {
            "state": Request.State.CANCELED,
            "decision": Request.Decision.CANCELED,
            "reason": comments,
        }

    def _error(self, comments):
        if self.request.has_finished():
            raise InvalidStateTransitionException(
                _("Current request has already finished")
            )

        if not comments:
            raise BlankParameterException(_("Failure reason is missing"))

        if self.request.is_parent():
            raise InvalidStateTransitionException(
                _("Only child level request can be flagged error")
            )

        return {
            "state": Request.State.FAILED,
            "decision": Request.Decision.ERROR,
            "reason": comments,
        }
