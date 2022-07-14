"""Default exception handler for all uncaught exceptions."""
import logging
from typing import Optional, Any, Dict

from django.contrib import auth
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from rest_framework.views import exception_handler, set_rollback
from rest_framework.response import Response
from rest_framework import status

from pinakes.common.auth.keycloak import exceptions as keycloak_exc

logger = logging.getLogger("django.request")


def custom_exception_handler(
    exc: Exception, context: Dict[str, Any]
) -> Optional[Response]:
    response = exception_handler(exc, context)
    if response is not None:
        return response

    # For all unhandled exceptions.
    logger.exception("Caught an internal exception:")

    message = _("Internal Error")
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(exc, IntegrityError):
        message = _(
            "{}. Report to the support team if it is not an user error."
        ).format(exc)
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, keycloak_exc.Unauthorized):
        auth.logout(context["request"])
        status_code = status.HTTP_403_FORBIDDEN
        message = _("Unauthorized")

    set_rollback()
    return Response(data={"detail": message}, status=status_code)
