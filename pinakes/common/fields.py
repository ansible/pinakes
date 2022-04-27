from typing import Dict

from rest_framework import serializers


class UserCapabilitiesField(serializers.ReadOnlyField):
    def __init__(self, **kwargs):
        kwargs["source"] = "*"
        super().__init__(**kwargs)

    def to_representation(self, value) -> Dict[str, bool]:
        request = self.context["request"]
        view = self.context["view"]

        keycloak_permission = view.get_keycloak_permission()
        permissions = keycloak_permission.get_user_capabilities(
            request, view, value
        )
        return permissions


class MetadataSerializer(serializers.Serializer):

    user_capabilities = UserCapabilitiesField()

    def __init__(self, skip_user_capabilities=False, **kwargs):
        kwargs["source"] = "*"
        kwargs["read_only"] = True
        super().__init__(**kwargs)

        if skip_user_capabilities:
            self.fields.pop("user_capabilities", None)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.update(getattr(instance, self.field_name, {}))
        return data
