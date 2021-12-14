from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Union

import pydantic

from .utils import to_lower_camel


class OpenIDConfiguration(pydantic.BaseModel):
    token_endpoint: str


class Uma2Configuration(pydantic.BaseModel):
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
    client_roles: Optional[List[str]] = None


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
