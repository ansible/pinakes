from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Union

import pydantic

from .utils import to_lower_camel


class OpenIDConfiguration(pydantic.BaseModel):
    token_endpoint: str


class Uma2Configuration(pydantic.BaseModel):
    token_endpoint: str
    resource_registration_endpoint: str
    permission_endpoint: str
    policy_endpoint: str


class ApiModelBase(pydantic.BaseModel):
    """Base model for Keycloak API resources."""

    class Config:
        alias_generator = to_lower_camel
        allow_population_by_field_name = True


class Group(ApiModelBase):
    """Keycloak group representation."""

    id: Optional[str] = None
    name: Optional[str] = None
    path: Optional[str] = None
    sub_groups: Optional[List[Group]] = None
    realm_roles: Optional[List[str]] = None
    client_roles: Optional[Dict[str, List[str]]] = None


Group.update_forward_refs()


class Scope(pydantic.BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None


class ResourceOwner(pydantic.BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None


class Resource(pydantic.BaseModel):
    id: Optional[str] = pydantic.Field(None, alias="_id")
    name: Optional[str] = None
    uris: Optional[List[str]] = None
    type: Optional[str] = None
    scopes: Optional[List[Scope]] = None
    icon_uri: Optional[str] = None
    owner: Optional[ResourceOwner] = None
    owner_managed_access: Optional[bool] = None
    display_name: Optional[str] = None
    attributes: Optional[Dict[str, List[str]]] = None

    class Config:
        alias_generator = to_lower_camel
        allow_population_by_field_name = True

    @pydantic.validator("owner", pre=True)
    def parse_owner(cls, value: Union[str, ResourceOwner]):
        if isinstance(value, str):
            value = ResourceOwner(id=value)
        return value

    @pydantic.validator("scopes", pre=True)
    def parse_scopes(cls, value: Sequence[Union[str, Scope]]):
        scopes = []
        for item in value:
            if isinstance(item, str):
                item = Scope(name=item)
            scopes.append(item)
        return scopes


class UmaPermission(pydantic.BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    roles: Optional[List[str]] = None
    groups: Optional[List[str]] = None
    clients: Optional[List[str]] = None
    users: Optional[List[str]] = None
    scopes: Optional[List[str]] = None


class User(pydantic.BaseModel):
    email: str
    username: str
    firstName: str
    lastName: str


@dataclass(frozen=True)
class AuthzPermission:
    resource: str = ""
    scope: str = ""

    def __post_init__(self):
        if not (self.resource or self.scope):
            raise ValueError("Both 'resource' and 'scope' cannot be empty.")

    def __str__(self):
        return f"{self.resource}#{self.scope}"

    @classmethod
    def parse(cls, value: str):
        resource, _, scope = value.partition("#")
        return cls(resource, scope)


class AuthzResource(pydantic.BaseModel):
    rsid: str
    rsname: str = ""
    scopes: Optional[List[str]] = None
