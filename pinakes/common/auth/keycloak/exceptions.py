"""Keycloak client exception classes.

Exception hierarchy:

* KeycloakError
  * HttpError
    * Unauthorized
    * Forbidden
    * NotFound
    * Conflict
  * ClientError
    * NoResultFound
    * MultipleResultsFound
"""
import requests
from typing import Optional


class KeycloakError(Exception):
    """Base class for all keycloak exceptions."""

    pass


class HttpError(KeycloakError):
    """Base class for HTTP exceptions."""

    def __init__(
        self,
        error: Optional[str] = None,
        error_description: Optional[str] = None,
        status_code: Optional[int] = None,
    ) -> None:
        if not error:
            error = "API Error"
        self.error = error
        self.error_description = error_description
        self.status_code = status_code

    def __str__(self) -> str:
        result = self.error
        if self.error_description:
            result += f": {self.error_description}"
        if self.status_code:
            result += f" (status: {self.status_code})"
        return result


class Unauthorized(HttpError):
    """HTTP 401 Unauthorized"""

    pass


class Forbidden(HttpError):
    """HTTP 403 Forbidden"""

    pass


class NotFound(HttpError):
    """HTTP 404 Not Found"""

    pass


class Conflict(HttpError):
    """HTTP 409 Conflict"""

    pass


class ClientError(KeycloakError):
    pass


class NoResultFound(ClientError):
    pass


class MultipleResultsFound(ClientError):
    pass


HTTP_EXCEPTIONS = {
    requests.codes.unauthorized: Unauthorized,
    requests.codes.forbidden: Forbidden,
    requests.codes.not_found: NotFound,
    requests.codes.conflict: Conflict,
}


def get_http_exception_class(status_code: int):
    """Return exception class for HTTP response status code."""
    return HTTP_EXCEPTIONS.get(status_code, HttpError)
