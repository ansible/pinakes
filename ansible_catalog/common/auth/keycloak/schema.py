from typing import List, Dict, Sequence, Union

import pydantic

from keycloak.utils import to_lower_camel


class Uma2Configuration(pydantic.BaseModel):
    authorization_endpoint: str
    token_endpoint: str
    introspection_endpoint: str
    registration_endpoint: str
    resource_registration_endpoint: str
    permission_endpoint: str
    policy_endpoint: str


class Scope(pydantic.BaseModel):
    id: str = None
    name: str = None


class ResourceOwner(pydantic.BaseModel):
    id: str = None
    name: str = None


class Resource(pydantic.BaseModel):
    id: str = pydantic.Field(None, alias="_id")
    name: str = None
    uris: List[str] = None
    type: str = None
    scopes: List[Scope] = None
    icon_uri: str = None
    owner: ResourceOwner = None
    owner_managed_access: bool = None
    display_name: str = None
    attributes: Dict[str, List[str]] = None

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
    id: str = None
    name: str = None
    description: str = None
    roles: List[str] = None
    groups: List[str] = None
    clients: List[str] = None
    users: List[str] = None
    scopes: List[str] = None
