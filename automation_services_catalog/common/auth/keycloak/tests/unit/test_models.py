import pytest

from automation_services_catalog.common.auth.keycloak import models


@pytest.mark.parametrize(
    ["permission", "resource", "scope"],
    [
        ("resource:abc", "resource:abc", ""),
        ("resource:abc#", "resource:abc", ""),
        ("#edit", "", "edit"),
        ("resource:abc#edit", "resource:abc", "edit"),
    ],
)
def test_parse_authz_permission(permission, resource, scope):
    p = models.AuthzPermission.parse(permission)
    assert p.resource == resource
    assert p.scope == scope


@pytest.mark.parametrize(
    ["permission"],
    [
        ("",),
        ("#",),
    ],
)
def test_parse_authz_permission_fail(permission):
    with pytest.raises(ValueError):
        models.AuthzPermission.parse(permission)
