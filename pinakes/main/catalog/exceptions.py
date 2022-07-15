"""Application specific exception classes"""
from rest_framework import exceptions, status
from django.utils.translation import gettext_lazy as _


class BadParamsException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Bad query parameters")


class InvalidSurveyException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Invalid survey")


class UncancelableException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Uncancelable Order")
