from typing import Protocol, Sequence, Tuple


class GroupProto(Protocol):
    id: str
    path: str


class KeycloakResourceProto(Protocol):
    keycloak_id: str

    def keycloak_type(self) -> str:
        ...

    def keycloak_actions(self) -> Sequence[str]:
        ...


def make_permission_name(obj: KeycloakResourceProto, group: GroupProto):
    return "group_{resource_type}_{resource_id}_{group_id}".format(
        resource_type=obj.keycloak_type(),
        resource_id=obj.keycloak_id,
        group_id=group.id,
    )


def make_scope(
    obj: KeycloakResourceProto, action: str, *, validate: bool = True
):
    type_ = obj.keycloak_type()
    if validate and action not in obj.keycloak_actions():
        raise ValueError(f"Invalid action '{action}' for resource '{type_}'.")
    return f"{type_}:{action}"


def parse_scope(obj: KeycloakResourceProto, scope: str):
    prefix = obj.keycloak_type() + ":"
    if scope.startswith(prefix):
        return scope[len(prefix) :]  # noqa: E203
    else:
        raise ValueError("Unexpected scope. Must begin with '{prefix}'.")


def make_scope_name(resource_type: str, permission: str) -> str:
    """Returns qualified Keycloak scope name."""
    return _make_name(resource_type, permission)


def make_resource_name(resource_type: str, resource_id: str) -> str:
    """Returns qualified Keycloak resource name."""
    return _make_name(resource_type, resource_id)


def parse_scope_name(scope_name: str) -> Tuple[str, str]:
    """Parses qualified Keycloak scope name.

    :return: Tuple of resource type and permission.
    """
    return _parse_name(scope_name)


def parse_resource_name(resource_name: str) -> Tuple[str, str]:
    """Parses qualified Keycloak resource name.

    :return: Tuple of resource type and resource ID.
    """
    return _parse_name(resource_name)


def _make_name(prefix: str, suffix: str) -> str:
    return f"{prefix}:{suffix}"


def _parse_name(name: str) -> Tuple[str, str]:
    prefix, _, suffix = name.rpartition(":")
    return prefix, suffix
