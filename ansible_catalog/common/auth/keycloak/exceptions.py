class ApiException(Exception):
    pass


class ResourceNotFound(ApiException):
    pass


class ResourceExists(ApiException):
    pass
