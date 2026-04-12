from __future__ import annotations

import json
from functools import lru_cache
from urllib.request import urlopen

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from .config import Settings, get_settings


bearer_scheme = HTTPBearer(auto_error=True)


class UserPrincipal(BaseModel):
    subject: str
    username: str
    email: str | None = None
    full_name: str | None = None
    roles: list[str]


@lru_cache
def _load_discovery_document(discovery_url: str) -> dict[str, str]:
    with urlopen(discovery_url) as response:
        return json.loads(response.read().decode("utf-8"))


@lru_cache
def _jwks_client(jwks_uri: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwks_uri)


def _decode_token(token: str, settings: Settings) -> dict:
    discovery = _load_discovery_document(settings.oidc_discovery_url)
    jwks_uri = discovery["jwks_uri"]
    if jwks_uri.startswith(settings.keycloak_public_url):
        jwks_uri = jwks_uri.replace(settings.keycloak_public_url, settings.keycloak_internal_url, 1)
    jwks_client = _jwks_client(jwks_uri)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=settings.keycloak_issuer,
        options={"verify_aud": False},
    )

    audience = payload.get("aud", [])
    authorized_party = payload.get("azp")
    audience_values = audience if isinstance(audience, list) else [audience]
    if settings.keycloak_client_id not in audience_values and authorized_party != settings.keycloak_client_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token audience mismatch")

    return payload


def get_current_principal(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> UserPrincipal:
    try:
        payload = _decode_token(credentials.credentials, settings)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}") from exc

    username = payload.get("preferred_username") or payload.get("email") or payload["sub"]
    full_name = payload.get("name")
    roles = payload.get("realm_access", {}).get("roles", [])

    return UserPrincipal(
        subject=payload["sub"],
        username=username,
        email=payload.get("email"),
        full_name=full_name,
        roles=roles,
    )


def require_roles(*required_roles: str):
    def _role_dependency(principal: UserPrincipal = Depends(get_current_principal)) -> UserPrincipal:
        if not any(role in principal.roles for role in required_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return principal

    return _role_dependency
