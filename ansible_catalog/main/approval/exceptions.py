"""Application specific exception classes"""
from rest_framework import exceptions, status

class InsufficientParamsException(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Insufficient query parameters"
