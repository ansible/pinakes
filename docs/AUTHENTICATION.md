# Authentication

The Pinakes project supports two authentication schemas:
  - Session authentication. Used for browser clients.
  - Bearer authentication. Used for standalone clients (e.g. CLI applications).

## Bearer authentication

To use Bearer authentication, client must first obtain access token from Keycloak directly.
Typically, a separate Keycloak client is required.

A standalone CLI application should create a public client and use
[OAuth 2.0 Device Authorization Grant](https://oauth.net/2/device-flow/) flow
to authenticate on Keycloak and receive tokens.

### Device flow

The [OAuth 2.0 Device Authorization Grant](https://oauth.net/2/device-flow/) 
(formerly known as the Device Flow) is intended for clients that have no browser or limited input 
capability to obtain an access token.

Keycloak supports the Device Flow for both public and confidential clients.
This chapter describes the Device Flow for a public client using an example of a CLI application.

To obtain a token using device flow, a standalone client must request a device code first:

```shell
$ CLIENT_ID=pinakes-cli
$ curl -X POST -d "client_id=$CLIENT_ID" \
  "http://localhost:8080/auth/realms/pinakes/protocol/openid-connect/auth/device" | jq
{
  "device_code": "<DEVICE_CODE>",
  "user_code": "JGVH-ZKBG",
  "verification_uri": "http://localhost:8080/auth/realms/pinakes/device",
  "verification_uri_complete": "http://localhost:8080/auth/realms/pinakes/device?user_code=JGVH-ZKBG",
  "expires_in": 600,
  "interval": 5
}
```

Then user should open the verification URL (`http://localhost:8080/auth/realms/pinakes/device`)
in their browser and enter the `user_code` value (`JGVH-ZKBG`), returned by previous request.

After user authentication and code verification is complete, standalone client may request
tokens by using the `device_code` received at previous step:

```shell
$ curl -X POST -d "grant_type=urn:ietf:params:oauth:grant-type:device_code" \
    -d "client_id=$CLIENT_ID" -d "device_code=<DEVICE_CODE>" \
    "http://localhost:8080/auth/realms/pinakes/protocol/openid-connect/token"
{
    "access_token": "eyJhb...",
    "expires_in": 300,
    "refresh_expires_in": 1800,
    "refresh_token": "05OD...",
    "token_type": "Bearer",
    "not-before-policy": 0,
    "session_state": "c708...",
    "scope": "profile email"
}  
```

### Audience configuration

Pinakes verifies audience of presented access token. This may require additional configuration
of a client or realm.

See [Keycloak: Audience Support](https://www.keycloak.org/docs/latest/server_admin/#audience-support)
for more details.

### Development environment

For debugging purposes the development environment you need to create a confidential 
Keycloak client with `Direct Access Grants Enabled` option enabled, which
allows usage of [OAuth 2.0 Password Grant](https://oauth.net/2/grant-types/password/).

_**Warning:** The Password Grant flow is deprecated and discouraged.
You should not use it in production._ 

Examples below use client named `pinakes-cli`. 

**Example:**

```shell
$ CLIENT_ID=pinakes-cli
$ ACCESS_TOKEN="$(curl -sS http://localhost:8080/auth/realms/pinakes/protocol/openid-connect/token \
    -d scope=openid -d grant_type=password -d client_id=$CLIENT_ID \
    -d username=fred.sample -d password=fred | jq -r .access_token)"
```

You can debug token payload:

```shell
echo $ACCESS_TOKEN | cut -d. -f2 | tr '+/' '-_' | base64 -d 2>/dev/null | jq
{
  "exp": 1656070300,
  "iat": 1656070000,
  "jti": "f715b6aa-062a-47fc-8c45-81460806040d",
  ...
}
```

After you received an access token, you can use it to access the API:

```shell
curl -sS -H "Authorization: Bearer $ACCESS_TOKEN" http://localhost:8000/api/pinakes/auth/me/
```

### Authentication backends

Pinakes provides two authentication backend classes, that implement Bearer authentication and
verify access tokens, issued by Keycloak:

- `KeycloakBearerOfflineAuthentication`. Performs an offline authentication, by verifying access
  token digital signature. Enabled by default.
- `KeycloakBearerOnlineAuthentication`. Verifies access token by calling Keycloak 
  token introspection endpoint.

These backends are mutually exclusive. At the moment it is not possible to switch between backends
by using environment variable settings.