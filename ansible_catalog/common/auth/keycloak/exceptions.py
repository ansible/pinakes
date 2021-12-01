class KeycloakError(Exception):
    pass


class ApiException(KeycloakError):
    pass


class ResourceNotFound(ApiException):
    pass


class ResourceExists(ApiException):
    pass


class ClientError(KeycloakError):
    pass


class NoResultFound(ClientError):
    pass


class MultipleResourcesFound(ClientError):
    pass
