"""default exception handler for all uncaught exceptions"""
from rest_framework.views import exception_handler, set_rollback
from rest_framework.response import Response
from rest_framework import status

import logging

logger = logging.getLogger("django.request")


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    # For all unhandled exceptions.
    if response is None:
        set_rollback()
        logger.exception("Caught an internal exception:")
        data = {"detail": "Internal Error"}
        response = Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response
