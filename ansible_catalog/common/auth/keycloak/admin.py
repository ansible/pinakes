from typing import Optional, List, Iterator

from . import constants
from . import models
from . import openid
from .client import ApiClient


GROUPS_PATH = "admin/realms/{realm}/groups"


class AdminClient:
    def __init__(self, server_url: str, realm: str, token: str):
        self._server_url = server_url.rstrip("/")
        self._realm = realm

        self._client = ApiClient(token=token)

    def list_groups(self) -> List[models.Group]:
        path = GROUPS_PATH.format(realm=self._realm)
        url = f"{self._server_url}/{path}"
        items = self._client.request_json("GET", url)
        return [models.Group.parse_obj(item) for item in items]

    def iter_group_members(
        self, group_id: str, max_prefetch: int = 100
    ) -> Iterator[models.User]:
        first = 0
        while True:
            objects = self.list_group_members(group_id, first, max_prefetch)
            if not objects:
                break
            yield from objects
            first += len(objects)

    def list_group_members(
        self, group_id: str, first: int, max_prefetch: int
    ) -> List[models.User]:
        path = constants.GROUP_MEMBERS_PATH.format(
            realm=self._realm, id=group_id
        )
        params = {"first": first, "max": max_prefetch}
        url = f"{self._server_url}/{path}"
        items = self._client.request_json("GET", url, params=params)
        return [models.User.parse_obj(item) for item in items]


def create_admin_client(
    server_url: str,
    realm: str,
    client_id: str = constants.ADMIN_CLI_CLIENT_ID,
    client_secret: Optional[str] = None,
) -> AdminClient:
    oidc_client = openid.OpenIdConnect(
        server_url, realm, client_id, client_secret
    )
    token_info = oidc_client.client_credentials_auth()
    return AdminClient(server_url, realm, token_info["access_token"])
