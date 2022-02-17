from typing import Optional


class KeycloakError(Exception):
    pass


class ApiException(KeycloakError):
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


class ResourceNotFound(ApiException):
    pass


class ResourceExists(ApiException):
    pass


class Forbidden(ApiException):
    pass


class ClientError(KeycloakError):
    pass


class NoResultFound(ClientError):
    pass


class MultipleResourcesFound(ClientError):
    pass
