"""Application specific exception classes"""
from rest_framework import exceptions, status
from django.utils.translation import gettext_lazy as _


class InsufficientParamsException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Insufficient query parameters")
