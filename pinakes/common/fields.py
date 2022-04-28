import copy
from typing import Dict

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
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


@extend_schema_field(OpenApiTypes.OBJECT)
class MetadataField(serializers.ReadOnlyField):
    def __init__(self, **kwargs):
        """
        Resource metadata field.

        Retrieves model instance metadata field combined
        with generated `user_capabilities`.

        User capabilities generation can be ignored by setting
        `user_capabilities_field` parameter to `None`:

            metadata = MetadataField(user_capabilities_field=None)

        Or it can be overridden by a custom field:

            metadata = MetadataField(
                user_capabilities_field=CustomUserCapabilitiesField()
            )
        """
        kwargs["source"] = "*"
        kwargs["default"] = {}
        try:
            self._user_capabilities_field = copy.deepcopy(
                kwargs.pop("user_capabilities_field")
            )
        except KeyError:
            self._user_capabilities_field = UserCapabilitiesField()

        super().__init__(**kwargs)

        if self._user_capabilities_field:
            self._user_capabilities_field.bind("", self)

    def to_representation(self, instance):
        if not instance:
            return {}
        data = {}
        if self._user_capabilities_field:
            data[
                "user_capabilities"
            ] = self._user_capabilities_field.to_representation(instance)
        metadata = getattr(instance, self.field_name, None)
        if metadata is not None:
            data.update(metadata)
        return data
