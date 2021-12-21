from rest_framework import views


class KeycloakPermissionMixin(views.APIView):

    keycloak_resource_type = None
    keycloak_access_policies = {}

    def get_keycloak_access_policies(self):
        return self.keycloak_access_policies
