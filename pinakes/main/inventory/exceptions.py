"""Application specific exception classes"""
from rest_framework import exceptions, status
from django.utils.translation import gettext_lazy as _


class RefreshAlreadyRegisteredException(exceptions.APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = _("Refresh already registered")


class SourceUnchangeableException(ValueError):
    pass
