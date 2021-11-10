from __future__ import annotations

from typing import List, Optional

import pydantic

from .utils import to_lower_camel


class OpenIDConfiguration(pydantic.BaseModel):
    token_endpoint: str


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
