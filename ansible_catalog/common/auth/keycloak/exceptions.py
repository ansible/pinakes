class KeycloakError(Exception):
    pass


class KeycloakRequestError(KeycloakError):
    def __init__(self, error: str = None, error_description: str = None):
        self.error = error
        self.error_description = error_description

    def __str__(self):
        return "{cls}: {error} {error_description}".format(
            cls=self.__class__.__name__,
            error=self.error,
            error_description=self.error_description,
        )
