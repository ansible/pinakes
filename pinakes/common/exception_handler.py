"""default exception handler for all uncaught exceptions"""
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _
from rest_framework.views import exception_handler, set_rollback
from rest_framework.response import Response
from rest_framework import status

import logging

logger = logging.getLogger("django.request")


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return response

    # For all unhandled exceptions.
    set_rollback()
    logger.exception("Caught an internal exception:")

    message = _("Internal Error")
    code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(exc, IntegrityError):
        message = _(
            "{}. Report to the support team if it is not an user error."
        ).format(exc)
        code = status.HTTP_400_BAD_REQUEST
    return Response({"detail": message}, code)
