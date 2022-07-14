"""Application specific exception classes"""
from rest_framework import exceptions, status
from django.utils.translation import gettext_lazy as _


class InsufficientParamsException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Insufficient query parameters")


class InvalidStateTransitionException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Invalid State Transition")


class BlankParameterException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Field cannot be blank")


class DuplicatedUuidException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Duplicated UUID for approver groups")


class NoAppoverRoleException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Group has no approver role")


class GroupNotExistException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Group does not exist")


class WorkflowIsLinkedException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("There are resource objects linked to the workflow")


class WorkflowInUseException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Workflow is in use")
