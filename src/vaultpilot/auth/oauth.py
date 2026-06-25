"""Bungie OAuth2 authorization-code flow primitives.

Key Bungie facts encoded here (see PLAN.md §2.1):

- Authorize URL: ``https://www.bungie.net/en/OAuth/Authorize``
- Token URL: ``https://www.bungie.net/Platform/App/OAuth/Token/``
- **No ``scope`` parameter** is sent — granted scope is fixed by the app's
  checkboxes on bungie.net.
- A Confidential app authenticates to the token endpoint with HTTP Basic
  (``client_id``:``client_secret``); every request also sends ``X-API-Key``.
- Access tokens last ~1h; refresh tokens up to 90 days (renewing to a 1-year cap).
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel

DEFAULT_AUTHORIZE_URL = "https://www.bungie.net/en/OAuth/Authorize"
DEFAULT_TOKEN_URL = "https://www.bungie.net/Platform/App/OAuth/Token/"


@dataclass
class OAuthConfig:
    client_id: str
    client_secret: str
    api_key: str
    redirect_uri: str
    authorize_url: str = DEFAULT_AUTHORIZE_URL
    token_url: str = DEFAULT_TOKEN_URL


class TokenResponse(BaseModel):
    """Parsed Bungie token-endpoint response."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: str | None = None
    refresh_expires_in: int | None = None
    membership_id: str | None = None


def generate_state() -> str:
    """A CSRF state nonce for the authorize request."""
    return secrets.token_urlsafe(24)


def build_authorize_url(config: OAuthConfig, state: str) -> str:
    """Build the Bungie authorize URL the user opens in a browser.

    Note: no ``scope`` parameter — Bungie ignores it and uses the app's
    configured scopes. ``redirect_uri`` is included so multi-redirect apps pick
    the right one.
    """
    params = {
        "client_id": config.client_id,
        "response_type": "code",
        "state": state,
        "redirect_uri": config.redirect_uri,
    }
    return f"{config.authorize_url}?{urlencode(params)}"


def _headers(config: OAuthConfig) -> dict[str, str]:
    return {
        "X-API-Key": config.api_key,
        "Content-Type": "application/x-www-form-urlencoded",
    }


def _post_token(config: OAuthConfig, data: dict[str, str], client: httpx.Client) -> TokenResponse:
    resp = client.post(
        config.token_url,
        data=data,
        headers=_headers(config),
        auth=httpx.BasicAuth(config.client_id, config.client_secret),
    )
    resp.raise_for_status()
    return TokenResponse.model_validate(resp.json())


def exchange_code(config: OAuthConfig, code: str, *, client: httpx.Client | None = None) -> TokenResponse:
    """Exchange an authorization ``code`` for access + refresh tokens."""
    data = {"grant_type": "authorization_code", "code": code}
    if client is not None:
        return _post_token(config, data, client)
    with httpx.Client(timeout=30) as owned:
        return _post_token(config, data, owned)


def refresh_tokens(config: OAuthConfig, refresh_token: str, *, client: httpx.Client | None = None) -> TokenResponse:
    """Exchange a ``refresh_token`` for a new access (and refresh) token."""
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    if client is not None:
        return _post_token(config, data, client)
    with httpx.Client(timeout=30) as owned:
        return _post_token(config, data, owned)
