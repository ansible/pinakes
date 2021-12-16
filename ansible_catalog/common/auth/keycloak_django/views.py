class KeycloakPermissionMixin:

    keycloak_resource_name = None
    keycloak_access_policies = {}

    def get_keycloak_access_policies(self):
        return self.keycloak_access_policies
